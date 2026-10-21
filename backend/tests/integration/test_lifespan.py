from fastapi.testclient import TestClient

from bosquevivo.api.app import create_app
from bosquevivo.core.config import get_settings
from bosquevivo.db.session import _default_factory, get_engine


def test_lifespan_starts_worker_and_serves_health(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("SATELLITE_PROVIDER", "fake")
    get_settings.cache_clear()
    get_engine.cache_clear()
    _default_factory.cache_clear()
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        assert client.app.state.worker.handlers.keys() >= {"calculate_audit", "generate_report"}
    get_settings.cache_clear()
    get_engine.cache_clear()
    _default_factory.cache_clear()
