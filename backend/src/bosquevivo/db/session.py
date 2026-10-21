from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from bosquevivo.core.config import get_settings
from bosquevivo.db import models
from bosquevivo.db.base import Base


def build_engine(url: str) -> Engine:
    parsed = make_url(url)
    is_sqlite = parsed.drivername.startswith("sqlite")
    if is_sqlite and parsed.database not in (None, "", ":memory:"):
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, future=True, connect_args={"check_same_thread": False})
    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _pragmas(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


@lru_cache
def get_engine() -> Engine:
    return build_engine(get_settings().database_url)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@lru_cache
def _default_factory() -> sessionmaker[Session]:
    return make_session_factory(get_engine())


def init_db(engine: Engine | None = None) -> None:
    assert models.Project
    Base.metadata.create_all(engine or get_engine())


@contextmanager
def get_session() -> Iterator[Session]:
    session = _default_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
