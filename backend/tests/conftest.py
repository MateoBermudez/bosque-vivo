import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from bosquevivo.api.app import create_app
from bosquevivo.api.deps import db_session
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.db import init_db, make_session_factory
from bosquevivo.db.base import Base
from bosquevivo.db.session import build_engine
from bosquevivo.db.urls import resolve_database_url

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")


def _engine():
    if TEST_DATABASE_URL:
        engine = build_engine(resolve_database_url(TEST_DATABASE_URL), pool="null")
        Base.metadata.drop_all(engine)
        return engine
    return create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )


@pytest.fixture
def session():
    engine = _engine()
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s
    if TEST_DATABASE_URL:
        Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(session: Session) -> Session:
    return session


@pytest.fixture
def client(session: Session):
    app = create_app()
    app.dependency_overrides[db_session] = lambda: session
    app.dependency_overrides[get_settings] = lambda: Settings(admin_token="secreto")
    return TestClient(app)
