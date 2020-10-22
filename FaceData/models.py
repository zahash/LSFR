from sqlalchemy import Column, Text, Integer, Float, ForeignKey
from sqlalchemy.schema import PrimaryKeyConstraint

from .base import Base


class AutoRepr:
    def __repr__(self):
        return str(self.__dict__)


class FData(Base, AutoRepr):
    __tablename__ = "fdata"

    vec_id = Column(Text)
    post_url = Column(Text)
    img_url = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint(vec_id),
        {},
    )

    def __init__(self, vec_id, post_url, img_url):
        self.vec_id = vec_id
        self.post_url = post_url
        self.img_url = img_url


class FEmbed(Base, AutoRepr):
    __tablename__ = "fembed"

    vec_id = Column(Text, ForeignKey("fdata.vec_id"))
    embed_idx = Column(Integer)
    embed_val = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint(vec_id, embed_idx),
        {},
    )

    def __init__(self, vec_id, embed_idx, embed_val):
        self.vec_id = vec_id
        self.embed_idx = embed_idx
        self.embed_val = embed_val


class FLoc(Base, AutoRepr):
    __tablename__ = "floc"

    vec_id = Column(Text, ForeignKey("fdata.vec_id"))
    loc_idx = Column(Integer)
    loc_val = Column(Integer)

    __table_args__ = (
        PrimaryKeyConstraint(vec_id, loc_idx),
        {},
    )

    def __init__(self, vec_id, loc_idx, loc_val):
        self.vec_id = vec_id
        self.loc_idx = loc_idx
        self.loc_val = loc_val
