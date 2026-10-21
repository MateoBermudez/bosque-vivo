import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

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
