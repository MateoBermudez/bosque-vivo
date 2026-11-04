import pytest

from bosquevivo.cli import main
from bosquevivo.core.config import get_settings
from bosquevivo.db import session as db_session_module
from bosquevivo.setup import (
    SetupReport,
    missing_keys,
    prepare_backend_env,
    prepare_web_env,
    read_env,
    write_env,
)

EXAMPLE = """APP_ENV=dev
# comentario
SATELLITE_PROVIDER=gee
ADMIN_TOKEN=
PHONE_HMAC_KEY=
GEMINI_API_KEY=
"""


def make_root(tmp_path):
    (tmp_path / "backend").mkdir()
    (tmp_path / "web").mkdir()
    (tmp_path / ".env.example").write_text(EXAMPLE, encoding="utf-8")
    return tmp_path


def test_write_env_keeps_comments_and_appends(tmp_path):
    path = tmp_path / ".env"
    path.write_text("# hola\nA=1\n", encoding="utf-8")
    write_env(path, {"A": "2", "B": "3"})
    assert path.read_text(encoding="utf-8") == "# hola\nA=2\nB=3\n"
    assert read_env(path) == {"A": "2", "B": "3"}


def test_prepare_generates_secrets_once(tmp_path):
    root = make_root(tmp_path)
    report = SetupReport()
    backend = prepare_backend_env(root, report)
    web = prepare_web_env(root, backend, 8000, report)
    values = read_env(backend)
    assert len(values["ADMIN_TOKEN"]) == 64 and len(values["PHONE_HMAC_KEY"]) == 64
    assert values["SATELLITE_PROVIDER"] == "open"
    web_values = read_env(web)
    assert web_values["ADMIN_TOKEN"] == values["ADMIN_TOKEN"]
    assert web_values["BV_DATA_SOURCE"] == "live" and len(web_values["SESSION_SECRET"]) == 64
    assert "# comentario" in backend.read_text(encoding="utf-8")
    second = SetupReport()
    prepare_backend_env(root, second)
    prepare_web_env(root, backend, 8000, second)
    assert second.generated == [] and second.created == []
    assert read_env(backend)["ADMIN_TOKEN"] == values["ADMIN_TOKEN"]


def test_missing_keys_lists_only_external_credentials():
    pending = missing_keys({"GEMINI_API_KEY": "x", "GEMINI_MODEL": "m"})
    features = [requirement.feature for requirement, _ in pending]
    assert "IA (Gemini, capa gratuita)" not in features
    assert any("SMTP" in feature for feature in features)


@pytest.fixture
def fresh_caches():
    yield
    get_settings.cache_clear()
    db_session_module.get_engine.cache_clear()
    db_session_module._default_factory.cache_clear()


def test_setup_command_end_to_end(tmp_path, capsys, monkeypatch, fresh_caches):
    root = make_root(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert main(["setup", "--root", str(root), "--admin", "jefe@elpoli.edu.co"]) == 0
    output = capsys.readouterr().out
    assert "generado: SESSION_SECRET" in output
    assert "proyectos en la base: 3" in output
    assert "acceso/restablecer?token=" in output
    assert "GEMINI_API_KEY" in output
    assert (root / "backend" / "data" / "bosquevivo.db").exists()


def test_database_requirement_and_url_option(tmp_path):
    assert any("PostgreSQL" in r.feature for r, _ in missing_keys({}))
    url = "postgresql://postgres.ref:[YOUR-PASSWORD]@aws-0-x.pooler.supabase.com:6543/postgres"
    pending = missing_keys({"DATABASE_URL": url})
    assert [keys for r, keys in pending if "PostgreSQL" in r.feature] == [["DATABASE_PASSWORD"]]
    complete = missing_keys({"DATABASE_URL": url, "DATABASE_PASSWORD": "x"})
    assert not any("PostgreSQL" in r.feature for r, _ in complete)
    root = make_root(tmp_path)
    backend = prepare_backend_env(root, SetupReport(), url)
    assert read_env(backend)["DATABASE_URL"] == url
