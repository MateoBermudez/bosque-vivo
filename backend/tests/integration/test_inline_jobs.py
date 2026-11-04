import json
from pathlib import Path

from bosquevivo.api.deps import db_session
from bosquevivo.assistant.client import CloudApiClient
from bosquevivo.assistant.signature import compute_signature
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.db.models import AuditRun, Incident, Job, Report
from tests.integration.test_whatsapp_flow import seeded

__all__ = ["seeded"]

ADMIN = {"X-Admin-Token": "secreto"}


def inline_settings(tmp_path, **extra) -> Settings:
    return Settings(
        admin_token="secreto",
        jobs_mode="inline",
        data_dir=tmp_path,
        phone_hmac_key="k",
        whatsapp_token="t",
        whatsapp_phone_number_id="1",
        whatsapp_app_secret="app-secret",
        **extra,
    )


def test_inline_mode_flag():
    assert Settings(jobs_mode="inline").inline_jobs
    assert not Settings(jobs_mode="worker").inline_jobs


def test_webhook_answers_within_the_request(client, db, tmp_path, monkeypatch):
    settings = inline_settings(tmp_path)
    client.app.dependency_overrides[get_settings] = lambda: settings
    client.app.dependency_overrides[db_session] = lambda: db
    monkeypatch.setattr("bosquevivo.jobs.tasks.get_settings", lambda: settings)
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(CloudApiClient, "send_text", lambda self, to, body: sent.append((to, body)))
    message = {"id": "w9", "from": "573001112233", "type": "text", "text": {"body": "hola"}}
    body = json.dumps({"entry": [{"changes": [{"value": {"messages": [message]}}]}]}).encode()
    response = client.post(
        "/webhook/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": compute_signature(body, "app-secret")},
    )
    assert response.status_code == 200
    assert db.query(Job).one().status == "done"
    assert len(sent) == 2 and "ACEPTO" in sent[1][1]


def test_inline_audit_without_processing_fails_cleanly(client, db, seeded, tmp_path):
    settings = inline_settings(tmp_path, satellite_provider="gee", gee_project="")
    client.app.dependency_overrides[get_settings] = lambda: settings
    response = client.post(f"/api/v1/projects/{seeded.id}/audit", headers=ADMIN)
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "failed" and "CLI" in job["error"]
    assert db.query(Incident).filter(Incident.component == "tarea:calculate_audit").count() == 1


def test_report_is_generated_on_demand_and_after_losing_the_file(client, db, seeded, tmp_path):
    client.app.dependency_overrides[get_settings] = lambda: inline_settings(tmp_path)
    run = db.query(AuditRun).filter(AuditRun.project_id == seeded.id).one()
    first = client.get(f"/api/v1/audits/{run.id}/report?format=html")
    assert first.status_code == 200 and "Reserva El Roble" in first.text
    Path(db.query(Report).one().path).unlink()
    again = client.get(f"/api/v1/audits/{run.id}/report?format=html")
    assert again.status_code == 200
    assert client.get("/api/v1/audits/999/report").status_code == 404
