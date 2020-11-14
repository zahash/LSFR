from sqlalchemy import Column, Text, Integer, Float
from sqlalchemy.schema import PrimaryKeyConstraint

from .base import Base


class AutoRepr:
    def __repr__(self):
        return str(self.__dict__)


class Index(Base, AutoRepr):
    __tablename__ = "findex"

    vec_id = Column(Text)
    hash_bucket = Column(Text)
    euc_bucket = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint(vec_id, hash_bucket, euc_bucket),
        {},
    )

    def __init__(self, vec_id, hash_bucket, euc_bucket):
        self.vec_id = vec_id
        self.hash_bucket = hash_bucket
        self.euc_bucket = euc_bucket


class HashTables(Base, AutoRepr):
    __tablename__ = "htables"

    htno = Column(Integer)
    i = Column(Integer)
    j = Column(Integer)
    val = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint(htno, i, j),
        {},
    )

    def __init__(self, htno, i, j, val):
        self.htno = htno
        self.i = i
        self.j = j
        self.val = val
