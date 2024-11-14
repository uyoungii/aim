import heapq
import logging
import os
import aimrocks

import cachetools.func

from pathlib import Path

from aim.storage.encoding import encode_path
from aim.storage.container import Container
from aim.storage.prefixview import PrefixView
from aim.storage.rockscontainer import RocksContainer, optimize_db_for_read

from typing import Dict, List, NamedTuple, Tuple


logger = logging.getLogger(__name__)


class Racer(NamedTuple):
    key: bytes
    priority: int
    value: bytes
    prefix: bytes
    iterator: 'aimrocks.ItemsIterator'


class ItemsIterator:
    def __init__(self, dbs: Dict[bytes, "aimrocks.DB"], *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._iterators = {}
        for key, value in dbs.items():
            self._iterators[key] = value.iteritems(*args, **kwargs)
        self._priority: Dict[bytes, int] = {
            prefix: idx
            for idx, prefix in enumerate(self._iterators)
        }
        self._heap: List[Racer] = []

    def __iter__(self):
        return self

    def __reversed__(self):
        raise NotImplementedError

    def seek_to_first(self):
        for prefix, iterator in self._iterators.items():
            iterator.seek_to_first()
        self._init_heap()

    def seek_to_last(self):
        for prefix, iterator in self._iterators.items():
            iterator.seek_to_last()
        self._init_heap()

    def seek(self, key: bytes):
        for prefix, iterator in self._iterators.items():
            iterator.seek(key)
        self._init_heap()

    def seek_for_prev(self, key):
        for prefix, iterator in self._iterators.items():
            iterator.seek_for_prev(key)
        max_key = self._init_heap()
        self.seek(max_key)

    def get(self) -> Tuple[bytes, bytes]:
        return self._get(seek_next=False)

    def _get(self, seek_next: bool = False) -> Tuple[bytes, bytes]:

        if not self._heap:
            raise StopIteration

        key, _, value, prefix, iterator = self._heap[0]

        if not seek_next:
            return key, value

        while self._heap:
            alt = self._heap[0]

            if (
                alt.key != key and (alt.prefix == prefix or not alt.key.startswith(prefix))
            ):
                break

            heapq.heappop(self._heap)
            try:
                new_key, new_value = next(alt.iterator)
                racer = Racer(new_key, alt.priority, new_value, alt.prefix, alt.iterator)
                heapq.heappush(self._heap, racer)
                # self._state[prefix] = (new_key, new_value)
            except StopIteration:
                pass

        return key, value

    def _init_heap(self):
        self._heap = []
        max_key = b''
        for prefix, iterator in self._iterators.items():
            try:
                key, value = iterator.get()
                max_key = max(key, max_key)
            except ValueError:
                continue
            racer = Racer(key, self._priority[prefix], value, prefix, iterator)
            heapq.heappush(self._heap, racer)

        return max_key

    def __next__(self) -> Tuple[bytes, bytes]:
        return self._get(seek_next=True)


# We temporary implement KeysIterator and ValuesIterator
# using ItemsIterator because the performance is not better
# when iterating over only one of them

class KeysIterator(ItemsIterator):

    def get(self) -> bytes:
        key, value = super().get()
        return key

    def __next__(self) -> bytes:
        key, value = super().__next__()
        return key


class ValuesIterator(ItemsIterator):
    def get(self) -> bytes:
        key, value = super().get()
        return value

    def __next__(self) -> bytes:
        key, value = super().__next__()
        return value


class DB(object):
    def __init__(self, db_path: str, db_name: str, opts, read_only: bool = False):
        assert read_only
        self.db_path = db_path
        self.db_name = db_name
        self.opts = opts
        self._dbs: Dict[bytes, aimrocks.DB] = dict()

    def _get_db(
        self,
        prefix: bytes,
        path: str,
        cache: Dict[bytes, aimrocks.DB],
        store: Dict[bytes, aimrocks.DB] = None,
    ):
        db = cache.get(prefix)
        if db is None:
            optimize_db_for_read(Path(path), self.opts)
            db = aimrocks.DB(path, opts=aimrocks.Options(**self.opts), read_only=True)
        if store is not None:
            store[prefix] = db
        return db

    @cachetools.func.ttl_cache(maxsize=None, ttl=0.1)
    def _list_dir(self, path: str):
        try:
            return os.listdir(path)
        except FileNotFoundError:
            return []

    @property
    @cachetools.func.ttl_cache(maxsize=None, ttl=0.1)
    def dbs(self):
        index_prefix = encode_path((self.db_name, "chunks"))
        index_path = os.path.join(self.db_path, self.db_name, "index")
        try:
            index_db = self._get_db(index_prefix, index_path, self._dbs)
        except Exception:
            index_db = None
            logger.warning('No index was detected')

        # If index exists -- only load those in progress
        selector = 'progress' if index_db is not None else 'chunks'

        new_dbs: Dict[bytes, aimrocks.DB] = {}
        db_dir = os.path.join(self.db_path, self.db_name, selector)
        for prefix in self._list_dir(db_dir):
            path = os.path.join(self.db_path, self.db_name, "chunks", prefix)
            prefix = encode_path((self.db_name, "chunks", prefix))
            self._get_db(prefix, path, self._dbs, new_dbs)

        if index_db is not None:
            new_dbs[b""] = index_db
        self._dbs = new_dbs
        return new_dbs

    def close(self):
        ...

    def get(self, key: bytes, *args, **kwargs) -> bytes:
        for prefix, db in self.dbs.items():
            # Shadowing
            if key.startswith(prefix):
                return db.get(key)
        return self.dbs[b""].get(key)

    def iteritems(
        self, *args, **kwargs
    ) -> "ItemsIterator":
        return ItemsIterator(self.dbs, *args, **kwargs)

    def iterkeys(
        self, *args, **kwargs
    ) -> "KeysIterator":
        return KeysIterator(self.dbs, *args, **kwargs)

    def itervalues(
        self, *args, **kwargs
    ) -> "ValuesIterator":
        return ValuesIterator(self.dbs, *args, **kwargs)


class RocksUnionContainer(RocksContainer):

    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    @property
    def writable_db(self) -> aimrocks.DB:
        raise NotImplementedError

    @property
    def db(self) -> aimrocks.DB:
        assert self.read_only

        if self._db is not None:
            return self._db
        try:
            logger.debug(f'opening {self.path} as aimrocks db')
            path = Path(self.path)
            path.parent.mkdir(parents=True, exist_ok=True)

            self._db = DB(str(path.parent), path.name, self._db_opts, read_only=self.read_only)
        except Exception as e:
            # print(e, self.path)
            raise e

        return self._db

    def view(
        self,
        prefix: bytes = b''
    ) -> 'Container':
        container = self
        if prefix and prefix in self.db.dbs:
            container = RocksUnionSubContainer(container=self, domain=prefix)
        return PrefixView(prefix=prefix,
                          container=container)


class RocksUnionSubContainer(RocksContainer):
    def __init__(self, container: 'RocksUnionContainer', domain: bytes):
        self._parent = container
        self.domain = domain

    @property
    def writable_db(self) -> aimrocks.DB:
        raise NotImplementedError

    @property
    def db(self) -> aimrocks.DB:
        db: DB = self._parent.db
        return db.dbs.get(self.domain, db)

    def view(
        self,
        prefix: bytes = b''
    ) -> 'Container':
        return PrefixView(prefix=prefix, container=self)
