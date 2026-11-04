from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Connection, Engine, create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from bosquevivo.core.config import get_settings
from bosquevivo.db import models
from bosquevivo.db.base import Base
from bosquevivo.db.urls import is_postgres, resolve_database_url

SQLITE_BUSY_SECONDS = 60


def build_engine(url: str, *, serverless: bool = False, pool: str = "auto") -> Engine:
    parsed = make_url(url)
    if is_postgres(parsed):
        options: dict = {"pool_pre_ping": True}
        if pool == "null" or (pool == "auto" and serverless):
            options["poolclass"] = NullPool
        return create_engine(
            url,
            future=True,
            connect_args={"prepare_threshold": None, "connect_timeout": 15},
            **options,
        )
    is_sqlite = parsed.drivername.startswith("sqlite")
    if is_sqlite and parsed.database not in (None, "", ":memory:"):
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        url, future=True, connect_args={"check_same_thread": False, "timeout": SQLITE_BUSY_SECONDS}
    )
    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _pragmas(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


def settings_url() -> str:
    settings = get_settings()
    return resolve_database_url(settings.database_url, settings.database_password)


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return build_engine(settings_url(), serverless=settings.serverless, pool=settings.db_pool)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@lru_cache
def _default_factory() -> sessionmaker[Session]:
    return make_session_factory(get_engine())


ADDED_COLUMNS: dict[str, dict[str, str]] = {
    "wa_user": {"project_id": "INTEGER REFERENCES project(id) ON DELETE SET NULL"},
    "password_reset_token": {"purpose": "VARCHAR(20) NOT NULL DEFAULT 'reset'"},
}


SCHEMA_LOCK = 814_251_026


def _upgrade(connection: Connection) -> list[str]:
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    applied: list[str] = []
    for table, columns in ADDED_COLUMNS.items():
        if table not in tables:
            continue
        present = {column["name"] for column in inspector.get_columns(table)}
        for name, ddl in columns.items():
            if name not in present:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                applied.append(f"{table}.{name}")
    return applied


def upgrade_schema(engine: Engine) -> list[str]:
    with engine.begin() as connection:
        return _upgrade(connection)


def init_db(engine: Engine | None = None) -> None:
    assert models.Project
    target = engine or get_engine()
    with target.begin() as connection:
        if is_postgres(target.url):
            connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SCHEMA_LOCK})
        Base.metadata.create_all(connection)
        _upgrade(connection)


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
