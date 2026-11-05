from pathlib import Path

from bosquevivo.core.config import Settings, get_settings
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.core.incidents import record_incident
from bosquevivo.db.models import AuditRun, Project
from bosquevivo.db.remote import push_database
from bosquevivo.db.session import build_engine, init_db, make_session_factory
from bosquevivo.db.snapshot import load_snapshot

SNAPSHOT = Path(__file__).resolve().parents[3] / "web" / "snapshot"
ADMIN = {"X-Admin-Token": "secreto"}


def snapshot_engine(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'snapshot.db'}")
    init_db(engine)
    with make_session_factory(engine)() as session:
        summary = load_snapshot(session, SNAPSHOT)
        session.commit()
    return engine, summary


def test_snapshot_loads_projects_series_and_audits(tmp_path):
    _, summary = snapshot_engine(tmp_path)
    assert summary.projects >= 50 and summary.audits > 0 and summary.observations > 0


def test_push_database_through_the_api(client, db, tmp_path):
    engine, summary = snapshot_engine(tmp_path)
    client.headers.update(ADMIN)
    report = push_database(engine, client)
    assert report.problems == []
    assert db.query(Project).count() == summary.projects
    assert db.query(AuditRun).count() == summary.audits
    again = push_database(engine, client)
    assert again.problems and "ya tiene datos" in again.problems[0]
    replaced = push_database(engine, client, replace=True)
    assert replaced.problems == []
    assert db.query(Project).count() == summary.projects


def test_restore_requires_admin_and_known_table(client):
    assert client.get("/api/v1/admin/restore").status_code == 401
    bad = client.post("/api/v1/admin/restore", headers=ADMIN, json={"table": "x", "rows": []})
    assert bad.status_code == 422
    wrong = client.post("/api/v1/admin/restore/clear", headers=ADMIN, json={"confirm": "si"})
    assert wrong.status_code == 422


def test_admin_invites_user_and_returns_link_without_smtp(client, tmp_path):
    client.app.dependency_overrides[get_settings] = lambda: Settings(
        admin_token="secreto", data_dir=tmp_path, mail_backend="outbox"
    )
    body = {"email": "Nueva@ElPoli.edu.co", "name": "Nueva"}
    created = client.post("/api/v1/admin/users/invite", headers=ADMIN, json=body).json()
    assert created["email"] == "nueva@elpoli.edu.co" and created["emailed"] is False
    assert "/acceso/restablecer?token=" in created["link"]
    duplicate = client.post("/api/v1/admin/users/invite", headers=ADMIN, json=body)
    assert duplicate.status_code == 422
    users = client.get("/api/v1/admin/users", headers=ADMIN).json()
    assert users == [{"email": "nueva@elpoli.edu.co", "name": "Nueva", "active": True}]
    assert client.post("/api/v1/admin/users/invite", json=body).status_code == 401


def test_admin_lists_recent_incidents(client, session):
    record_incident(session, "ia", ExternalServiceError("modelo saturado (503)"), origin="externo")
    session.commit()
    assert client.get("/api/v1/admin/incidents").status_code == 401
    body = client.get("/api/v1/admin/incidents?days=7", headers=ADMIN).json()
    assert body["summary"]["total"] == 1 and body["summary"]["externos"] == 1
    row = body["incidents"][0]
    assert row["component"] == "ia" and "503" in row["cause"]


def test_gemini_model_defaults_to_latest_aliases():
    settings = Settings(gemini_model="", gemini_model_light="")
    assert settings.llm_model == "gemini-flash-latest"
    assert settings.llm_model_light == "gemini-flash-lite-latest"
    assert Settings(gemini_model="otro").llm_model == "otro"


def test_admin_mail_test(client, tmp_path):
    client.app.dependency_overrides[get_settings] = lambda: Settings(
        admin_token="secreto", data_dir=tmp_path, mail_backend="outbox"
    )
    response = client.post("/api/v1/admin/mail-test", headers=ADMIN, json={"to": "a@b.co"})
    assert response.json() == {"backend": "outbox", "to": "a@b.co"}
    assert len(list((tmp_path / "outbox").glob("*.eml"))) == 1
