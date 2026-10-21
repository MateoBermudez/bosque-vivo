import json
from datetime import date

import pytest

from bosquevivo.ai.agent import Agent, default_registry
from bosquevivo.ai.llm import LLMResponse, ScriptedLLM, ToolCall
from bosquevivo.api.deps import db_session
from bosquevivo.assistant import AssistantService, IncomingMessage
from bosquevivo.assistant.client import RecordingClient
from bosquevivo.assistant.signature import compute_signature
from bosquevivo.audit import AuditService
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.core.privacy import phone_hmac
from bosquevivo.db.models import AgentRun, ConsentLog, Evidence, Job, Project, WaUser
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.providers import FakeProvider

PHONE = "573001112233"
RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]
SETTINGS = Settings(phone_hmac_key="clave-hmac-de-prueba", whatsapp_app_secret="app-secret")


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


def build(db, script, media=None):
    llm = ScriptedLLM(script)
    client = RecordingClient(media)
    agent = Agent(db, llm, default_registry(), SETTINGS)
    return AssistantService(db, agent, client, llm, SETTINGS), client, llm


def text(message_id, body):
    return IncomingMessage(message_id=message_id, phone=PHONE, kind="text", text=body)


def onboard(service):
    service.handle(text("m0", "hola"))
    service.handle(text("m1", "ACEPTO"))


def test_first_contact_sends_welcome_and_notice_without_calling_model(db):
    service, client, llm = build(db, [])
    service.handle(text("m0", "hola"))
    assert len(client.sent) == 2
    assert "inteligencia artificial" in client.sent[0][1]
    assert "tercero" in client.sent[1][1]
    assert llm.calls == []


def test_phone_is_stored_only_as_hmac(db):
    service, _, _ = build(db, [])
    service.handle(text("m0", "hola"))
    user = db.query(WaUser).one()
    assert PHONE not in user.phone_hmac
    assert user.phone_hmac == phone_hmac(PHONE, SETTINGS.phone_hmac_key)


def test_questions_before_consent_are_not_answered(db):
    service, client, llm = build(db, [])
    service.handle(text("m0", "hola"))
    client.sent.clear()
    service.handle(text("m1", "¿cómo está el bosque?"))
    assert "ACEPTO" in client.sent[0][1]
    assert llm.calls == []


def test_consent_is_logged_with_notice_version(db):
    service, _, _ = build(db, [])
    onboard(service)
    log = db.query(ConsentLog).one()
    assert log.purpose == "datos" and log.notice_version == "v1" and log.granted


def test_answer_after_consent_respects_length(db, seeded):
    script = [
        ToolCallResponse("obtener_auditoria", proyecto_id=seeded.id),
        LLMResponse(text="El bosque tiene correspondencia alta, con confianza alta."),
    ]
    service, client, _ = build(db, script)
    onboard(service)
    client.sent.clear()
    service.handle(text("m2", "¿Cómo está el Roble?"))
    assert len(client.sent) == 1
    assert len(client.sent[0][1]) <= 300


def ToolCallResponse(name, **args):
    return LLMResponse(tool_calls=[ToolCall(name, args)])


def test_duplicate_message_is_processed_once(db):
    service, client, _ = build(db, [])
    service.handle(text("m0", "hola"))
    service.handle(text("m0", "hola"))
    assert len(client.sent) == 2


def test_delete_command_removes_user_consents_and_traces(db, seeded):
    script = [LLMResponse(text="Hola, ¿en qué le ayudo?")]
    service, client, _ = build(db, script)
    onboard(service)
    service.handle(text("m2", "hola"))
    assert db.query(AgentRun).count() == 1
    client.sent.clear()
    service.handle(text("m3", "borrar mis datos"))
    assert db.query(WaUser).count() == 0
    assert db.query(ConsentLog).count() == 0
    assert db.query(AgentRun).count() == 0
    assert "Borré" in client.sent[0][1]


def test_delete_command_also_removes_evidence_of_the_user_queries(db, seeded):
    script = [
        ToolCallResponse("obtener_auditoria", proyecto_id=seeded.id),
        LLMResponse(text="Hay correspondencia alta con confianza alta."),
    ]
    service, _, _ = build(db, script)
    onboard(service)
    service.handle(text("m2", "estado"))
    assert db.query(Evidence).count() == 1
    service.handle(text("m3", "borrar mis datos"))
    assert db.query(Evidence).count() == 0


def test_photo_requires_separate_consent(db, seeded):
    media = {"img1": (b"jpeg", "image/jpeg")}
    service, client, llm = build(db, [], media)
    onboard(service)
    client.sent.clear()
    service.handle(
        IncomingMessage(
            message_id="p1", phone=PHONE, kind="image", media_id="img1", mime_type="image/jpeg"
        )
    )
    assert "ACEPTO FOTOS" in client.sent[0][1]
    assert llm.calls == []


def test_audio_is_transcribed_then_answered(db, seeded):
    media = {"aud1": (b"ogg", "audio/ogg")}
    script = [
        LLMResponse(text="cómo está el bosque"),
        LLMResponse(text="Todavía no tengo datos para concluir."),
    ]
    service, client, llm = build(db, script, media)
    onboard(service)
    service.handle(text("m2", "acepto fotos"))
    client.sent.clear()
    service.handle(
        IncomingMessage(
            message_id="a1", phone=PHONE, kind="audio", media_id="aud1", mime_type="audio/ogg"
        )
    )
    assert llm.calls[0]["messages"][0].media[0].mime_type == "audio/ogg"
    assert client.sent


def test_unintelligible_audio_asks_to_write(db, seeded):
    media = {"aud1": (b"ogg", "audio/ogg")}
    service, client, _ = build(db, [LLMResponse(text="NO_ENTENDIDO")], media)
    onboard(service)
    service.handle(text("m2", "acepto fotos"))
    client.sent.clear()
    service.handle(
        IncomingMessage(
            message_id="a1", phone=PHONE, kind="audio", media_id="aud1", mime_type="audio/ogg"
        )
    )
    assert "escribirme" in client.sent[0][1]


def test_location_message_is_passed_to_agent(db, seeded):
    script = [
        ToolCallResponse("buscar_proyecto"),
        LLMResponse(text="Ese lugar está en un proyecto registrado."),
    ]
    service, _, llm = build(db, script)
    onboard(service)
    service.handle(
        IncomingMessage(
            message_id="l1", phone=PHONE, kind="location", latitude=5.05, longitude=-74.95
        )
    )
    assert "lat 5.05" in llm.calls[0]["messages"][0].text
    tool_result = llm.calls[1]["messages"][-1].tool_results[0].content
    assert tool_result["nombre"] == "Reserva El Roble"


def test_webhook_rejects_bad_signature(client):
    body = json.dumps({"entry": []}).encode()
    response = client.post(
        "/webhook/whatsapp", content=body, headers={"X-Hub-Signature-256": "sha256=bad"}
    )
    assert response.status_code == 401


def test_webhook_enqueues_job_for_valid_signature(client, db):
    client.app.dependency_overrides[get_settings] = lambda: SETTINGS
    client.app.dependency_overrides[db_session] = lambda: db
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "w1",
                                    "from": PHONE,
                                    "type": "text",
                                    "text": {"body": "hola"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    body = json.dumps(payload).encode()
    response = client.post(
        "/webhook/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": compute_signature(body, "app-secret")},
    )
    assert response.status_code == 200
    job = db.query(Job).one()
    assert job.kind == "whatsapp_message" and job.payload["message_id"] == "w1"


def test_webhook_verification_handshake(client):
    client.app.dependency_overrides[get_settings] = lambda: Settings(whatsapp_verify_token="vt")
    ok = client.get(
        "/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "vt", "hub.challenge": "123"},
    )
    assert ok.status_code == 200 and ok.text == "123"
    bad = client.get(
        "/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "x", "hub.challenge": "123"},
    )
    assert bad.status_code == 403
