from contextlib import contextmanager
from datetime import datetime
from logging import Logger, getLogger
from typing import Type, Iterable, List, Set, Union

from praw import Reddit
from praw.models import Submission
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from soccer_helper.config import Config
from soccer_helper.models import Base

log: Logger = getLogger(__name__)


class DataStore:

    def __init__(self, config: Config, reddit: Reddit):
        self._config: Config = config
        self._reddit: Reddit = reddit
        self._delete_set: Set[Base] =set()
        self._update_set: Set[Base] = set()
        self.engine = create_engine(config.database_uri)
        # noinspection PyTypeChecker
        self._Session: Type[Session] = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self) -> Session:
        session = self._Session()
        try:
            self._delete_set.clear()
            self._update_set.clear()
            yield session
            session.add_all(self._update_set)
            for obj in self._delete_set:
                session.delete(obj)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def enqueue_deletion(self, obj: Base):
        self._delete_set.add(obj)

    def mark_updated(self, obj: Base):
        self._update_set.add(obj)
