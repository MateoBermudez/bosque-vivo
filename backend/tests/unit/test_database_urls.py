import pytest
from sqlalchemy.pool import NullPool

from bosquevivo.db.session import build_engine
from bosquevivo.db.urls import describe, resolve_database_url

SUPABASE = (
    "postgresql://postgres.abc:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
)


def test_sqlite_is_untouched():
    assert resolve_database_url("sqlite:///data/bosquevivo.db") == "sqlite:///data/bosquevivo.db"


def test_supabase_placeholder_driver_and_ssl():
    url = resolve_database_url(SUPABASE, "p@ss/w:rd")
    assert url.startswith("postgresql+psycopg://postgres.abc:p%40ss%2Fw%3Ard@")
    assert url.endswith("sslmode=require")
    assert "p@ss" not in describe(url)


def test_placeholder_without_password_fails():
    with pytest.raises(ValueError, match="DATABASE_PASSWORD"):
        resolve_database_url(SUPABASE)


def test_postgres_scheme_alias_and_local_without_ssl():
    url = resolve_database_url("postgres://u:p@localhost:5432/db")
    assert url == "postgresql+psycopg://u:p@localhost:5432/db"


def test_serverless_uses_null_pool():
    engine = build_engine(
        resolve_database_url("postgresql://u:p@db.example.com/x"), serverless=True
    )
    assert isinstance(engine.pool, NullPool)
    assert build_engine("sqlite://").dialect.name == "sqlite"
