from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy import Integer, Text, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declarative_base

import uuid
import datetime

Base = declarative_base()


def get_uuid():
    return str(uuid.uuid4())


def default_to_run_hash(context):
    return f'Run: {context.get_current_parameters()["hash"]}'


run_tags = Table(
    'run_tag', Base.metadata,
    Column('run_id', Integer, ForeignKey('run.id'), primary_key=True, nullable=False),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True, nullable=False)
)


class Run(Base):
    __tablename__ = 'run'

    id = Column(Integer, autoincrement=True, primary_key=True)
    # TODO: [AT] make run_hash immutable
    hash = Column(Text, index=True, unique=True, nullable=False)
    name = Column(Text, default=default_to_run_hash)
    description = Column(Text, nullable=True)

    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    finalized_at = Column(DateTime, default=None)

    # relationships
    experiment_id = Column(ForeignKey('experiment.id'), nullable=True)

    experiment = relationship('Experiment', backref=backref('runs', uselist=True))
    tags = relationship('Tag', secondary=run_tags, backref=backref('runs', uselist=True))

    def __init__(self, run_hash):
        self.hash = run_hash


class Experiment(Base):
    __tablename__ = 'experiment'

    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(Text, index=True, unique=True, default=get_uuid)
    name = Column(Text, nullable=False, unique=True)
    is_archived = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __init__(self, name):
        self.name = name


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(Text, index=True, unique=True, default=get_uuid)
    name = Column(Text, nullable=False, unique=True)
    color = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __init__(self, name):
        self.name = name

    @validates('color')
    def validate_color(self, _, color):
        # TODO: [AT] add color validation
        return color
