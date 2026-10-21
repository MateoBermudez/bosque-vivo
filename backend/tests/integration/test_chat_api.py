import json
from datetime import date

import pytest

from bosquevivo.ai.llm import LLMResponse, ScriptedLLM, ToolCall
from bosquevivo.api.deps import get_llm, get_satellite_provider
from bosquevivo.audit import AuditService
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.db.models import Project
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.providers import FakeProvider

ADMIN = {"X-Admin-Token": "secreto"}
RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]


@pytest.fixture
def seeded(db, tmp_path):
    project = Project(
        source_registry="test",
        registry_id="1",
        name="Reserva El Roble",
        start_year=2018,
        area_ha=1000.0,
        geometry=json.dumps({"type": "Polygon", "coordinates": [RING]}),
        source="test",
    )
    db.add(project)
    db.commit()
    sat = SatelliteService(db, FakeProvider(), tmp_path)
    sat.refresh_timeseries(
        project.id, date(2016, 1, 1), date(2024, 12, 31), sensors=(Sensor.SENTINEL2,)
    )
    sat.refresh_forest_loss(project.id)
    AuditService(db).run(project.id)
    db.commit()
    return project


def test_chat_requires_admin_token(client):
    assert client.post("/api/v1/chat", json={"message": "hola"}).status_code == 401


def test_chat_returns_answer_with_evidence_and_trace(client, seeded):
    script = [
        LLMResponse(tool_calls=[ToolCall("obtener_auditoria", {"proyecto_id": seeded.id})]),
        LLMResponse(text="El proyecto tiene correspondencia alta con confianza alta."),
    ]
    client.app.dependency_overrides[get_llm] = lambda: ScriptedLLM(script)
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    response = client.post("/api/v1/chat", headers=ADMIN, json={"message": "estado del Roble"})
    assert response.status_code == 200
    data = response.json()
    assert data["tools_called"] == ["obtener_auditoria"] and not data["used_fallback"]
    traces = client.get("/api/v1/traces", headers=ADMIN).json()
    assert traces[0]["id"] == data["run_id"] and traces[0]["tools"] == ["obtener_auditoria"]


def test_chat_rejects_empty_message(client):
    client.app.dependency_overrides[get_llm] = lambda: ScriptedLLM([])
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    assert client.post("/api/v1/chat", headers=ADMIN, json={"message": ""}).status_code == 422


def test_chat_returns_503_when_model_is_not_configured(client):
    def missing():
        raise ExternalServiceError("GEMINI_API_KEY y GEMINI_MODEL son obligatorios")

    client.app.dependency_overrides[get_llm] = missing
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    response = client.post("/api/v1/chat", headers=ADMIN, json={"message": "hola"})
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]
