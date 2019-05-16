from datetime import datetime
from re import match

from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean

Base = declarative_base()


class TrackedObject(Base):

    __tablename__ = 'tracked_objects'

    fullname = Column(String, primary_key=True)
    added = Column(DateTime, default=datetime.now, nullable=False)
    track_until = Column(DateTime, nullable=False)
    tracking = Column(Boolean, default=False, nullable=False)
    type = Column(String, nullable=False)
    related_comment_id = Column(String, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": type
    }

    @property
    def id(self):
        return self.fullname[3:]

    @validates('fullname')
    def validates_fullname(self, key, fullname):
        assert match(r't[1-6]_[a-z0-9]+', fullname)
        return fullname


class TrackedSubmission(TrackedObject):

    TYPE = 't3'

    __mapper_args__ = {
        "polymorphic_identity": TYPE
    }


class TrackedComment(TrackedObject):

    TYPE = 't1'

    __mapper_args__ = {
        "polymorphic_identity": TYPE
    }


class Mirror(Base):

    __tablename__ = 'mirrors'

    original_url = Column(String, primary_key=True)
    mirror_url = Column(String, nullable=True)
    processing = Column(Boolean, default=False, nullable=False)
    skip = Column(Boolean, default=False, nullable=False)