import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from bosquevivo.api.app import create_app
from bosquevivo.api.deps import db_session
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.db import init_db, make_session_factory


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


@pytest.fixture
def db(session: Session) -> Session:
    return session


@pytest.fixture
def client(session: Session):
    app = create_app()
    app.dependency_overrides[db_session] = lambda: session
    app.dependency_overrides[get_settings] = lambda: Settings(admin_token="secreto")
    return TestClient(app)
