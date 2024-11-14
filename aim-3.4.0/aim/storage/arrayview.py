import numpy as np
from itertools import islice

from typing import Any, Generic, Iterator, List, TYPE_CHECKING, Tuple, TypeVar, Union
if TYPE_CHECKING:
    from .treeview import TreeView


T = TypeVar("T")


class ArrayView(Generic[T]):
    """Array of homogeneous elements with sparse indices.
    Interface for working with array as a non-sparse array is available for cases
    when index values are not important.
    """

    def __iter__(self) -> Iterator[T]:
        ...

    def keys(self) -> Iterator[int]:
        """Return sparse indices iterator.

        Yields:
             Array's next sparse index.
        """
        ...

    def indices(self) -> Iterator[int]:
        """Return sparse indices iterator.

        Yields:
             Array's next sparse index.
        """
        ...

    def values(self) -> Iterator[T]:
        """Return values iterator.

        Yields:
             Array's next value.
        """
        ...

    def items(self) -> Iterator[Tuple[int, T]]:
        """Return items iterator.

        Yields:
            Tuple of array's next sparse index and value.
        """
        ...

    # TODO [AT]: maybe we need to have a view(slice) method instead?
    # TODO [AT]: it will have the same ArrayView interface but implement values, items, ... with slicing logic
    def values_slice(self, _slice: slice, slice_by: str = 'step') -> Iterator[T]:
        ...

    def items_slice(self, _slice: slice, slice_by: str = 'step') -> Iterator[Tuple[int, T]]:
        ...

    def values_in_range(self, start, stop, count=None) -> Iterator[T]:
        ...

    def items_in_range(self, start, stop, count=None) -> Iterator[Tuple[int, T]]:
        ...

    def __len__(self) -> int:
        ...

    def __getitem__(
        self,
        idx: Union[int, slice]
    ) -> T:
        ...

    # TODO implement append

    def __setitem__(
        self,
        idx: int,
        val: Any
    ):
        ...

    def sparse_list(self) -> Tuple[List[int], List[T]]:
        """Get sparse indices and values as :obj:`list`s.
        """
        ...

    def indices_list(self) -> List[int]:
        """Get sparse indices as a :obj:`list`.
        """
        ...

    def values_list(self) -> List[T]:
        """Get values as a :obj:`list`.
        """
        ...

    def sparse_numpy(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get sparse indices and values as numpy arrays.
        """
        ...

    def indices_numpy(self) -> np.ndarray:
        """Get sparse indices as numpy array.
        """
        ...

    def values_numpy(self) -> np.ndarray:
        """Get values as numpy array.
        """
        ...

    def tolist(self) -> List[T]:
        """Convert to values list"""
        ...

    def first(self) -> Tuple[int, T]:
        """First index and value of the array.
        """
        ...

    def first_idx(self) -> int:
        """First index of the array.
        """
        ...

    def first_value(self) -> T:
        """First value of the array.
        """
        ...

    def last(self) -> Tuple[int, T]:
        """Last index and value of the array.
        """
        ...

    def last_idx(self) -> int:
        """Last index of the array.
        """
        ...

    def last_value(self) -> T:
        """Last value of the array.
        """
        ...

    def min_idx(self) -> int:
        ...

    def max_idx(self) -> int:
        ...


class TreeArrayView(ArrayView[T]):
    def __init__(
        self,
        tree: 'TreeView',
        dtype: Any = None
    ):
        self.tree = tree
        self.dtype = dtype

    def allocate(self):
        self.tree.make_array()
        return self

    def __iter__(self) -> Iterator[T]:
        yield from self.values()

    def keys(self) -> Iterator[int]:
        yield from self.tree.keys()

    def indices(self) -> Iterator[int]:
        yield from self.keys()

    def values(self) -> Iterator[T]:
        for k, v in self.tree.items():
            yield v

    def items(self) -> Iterator[Tuple[int, T]]:
        yield from self.tree.items()

    def values_slice(self, _slice: slice, slice_by: str = 'step') -> Iterator[T]:
        for k, v in self.items_slice(_slice, slice_by):
            yield v

    # TODO [AT]: improve performance (move to cython?)
    def items_slice(self, _slice: slice, slice_by: str = 'step') -> Iterator[Tuple[int, T]]:
        start, stop, step = _slice.start, _slice.stop, _slice.step
        if start < 0 or stop < 0 or step < 0:
            raise NotImplementedError('Negative index slices are not supported')
        if step == 0:
            raise ValueError('slice step cannot be zero')
        if stop <= start:
            return

        if slice_by == 'index':
            yield from islice(self.items(), start, stop, step)
        elif slice_by == 'step':
            items_ = self.items()

            # TODO [AT]: tidy-up the rest of the method
            # find fist item which has index matching the slice
            for idx, val in items_:
                if idx >= start:
                    if idx == start:
                        yield idx, val
                    break

            if step == 1:
                for idx, val in items_:
                    if stop is not None and idx >= stop:
                        break
                    yield idx, val
            else:
                for idx, val in items_:
                    if stop is not None and idx >= stop:
                        break
                    if (idx - start) % step == 0:
                        yield idx, val

    def values_in_range(self, start, stop, count=None) -> Iterator[T]:
        for k, v in self.items_in_range(start, stop, count):
            yield v

    def items_in_range(self, start, stop, count=None) -> Iterator[Tuple[int, T]]:
        if stop <= start or start < 0 or stop < 0:
            return

        items_ = self.items()
        items_in_range = []
        for idx, val in items_:
            if start <= idx < stop:
                items_in_range.append((idx, val))
            if idx >= stop:
                break
        step = (len(items_in_range) // count or 1) if count else 1
        yield from islice(items_in_range, 0, len(items_in_range), step)

    def __len__(self) -> int:
        # TODO lazier
        try:
            last_idx = self.last_idx()
        except KeyError:
            return 0
        return last_idx + 1

    def __bool__(self) -> bool:
        return bool(len(self))

    def __getitem__(
        self,
        idx: Union[int, slice]
    ) -> T:
        if isinstance(idx, slice):
            raise NotImplementedError
        return self.tree[idx]

    # TODO implement append

    def __setitem__(
        self,
        idx: int,
        val: Any
    ):
        assert isinstance(idx, int)
        self.tree[idx] = val

    def sparse_list(self) -> Tuple[List[int], List[T]]:
        indices = []
        values = []
        for k, v in self.items():
            indices.append(k)
            values.append(v)

        return indices, values

    def indices_list(self) -> List[int]:
        return list(self.indices())

    def values_list(self) -> List[T]:
        return list(self.values())

    def sparse_numpy(self) -> Tuple[np.ndarray, np.ndarray]:
        # TODO URGENT implement using cython
        indices_list, values_list = self.sparse_list()
        indices_array = np.array(indices_list, dtype=np.intp)
        values_array = np.array(values_list, dtype=self.dtype)
        return indices_array, values_array

    def indices_numpy(self) -> np.ndarray:
        # TODO URGENT implement using cython
        return np.array(self.indices_list(), dtype=np.intp)

    def values_numpy(self) -> np.ndarray:
        # TODO URGENT implement using cython
        return np.array(self.values_list(), dtype=self.dtype)

    def tolist(self) -> List[T]:
        arr = self.tree[...]
        assert isinstance(arr, list)
        return arr

    def first(self) -> Tuple[int, T]:
        idx = self.min_idx()
        return idx, self[idx]

    def first_idx(self) -> int:
        return self.min_idx()

    def first_value(self) -> T:
        return self[self.min_idx()]

    def last(self) -> Tuple[int, T]:
        idx = self.max_idx()
        return idx, self[idx]

    def last_idx(self) -> int:
        return self.max_idx()

    def last_value(self) -> T:
        return self[self.max_idx()]

    def min_idx(self) -> int:
        return self.tree.first()

    def max_idx(self) -> int:
        return self.tree.last()
