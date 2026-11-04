from bosquevivo.ai.llm import ScriptedLLM, UnavailableLLM
from bosquevivo.api.deps import get_assistant_llm, get_satellite_provider
from bosquevivo.db.models import WaUser
from tests.integration.test_whatsapp_flow import seeded

__all__ = ["seeded"]

ADMIN = {"X-Admin-Token": "secreto"}
REF = "a1b2c3d4-e5f6"


def send(client, message, ref=REF):
    return client.post(
        "/api/v1/community/messages", headers=ADMIN, json={"session_ref": ref, "message": message}
    )


def test_requires_admin_token(client):
    response = client.post(
        "/api/v1/community/messages", json={"session_ref": REF, "message": "hola"}
    )
    assert response.status_code == 401


def test_web_chat_follows_consent_and_intents(client, db, seeded):
    client.app.dependency_overrides[get_assistant_llm] = lambda: ScriptedLLM([])
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    first = send(client, "hola").json()["replies"]
    assert len(first) == 2 and "ACEPTO" in first[1]
    assert "ACEPTO" in send(client, "¿cómo está?").json()["replies"][0]
    send(client, "ACEPTO")
    assert "Reserva El Roble" in send(client, f"proyecto {seeded.id}").json()["replies"][0]
    status = send(client, "estado").json()["replies"][0]
    assert "se conserva" in status
    user = db.query(WaUser).one()
    assert "web" not in user.phone_hmac and len(user.phone_hmac) == 64
    assert "Borré" in send(client, "BORRAR MIS DATOS").json()["replies"][0]
    assert db.query(WaUser).count() == 0


def test_rejects_bad_session_ref(client):
    assert send(client, "hola", ref="../../x").status_code == 422


def test_works_without_gemini_key(client, db, seeded):
    client.app.dependency_overrides[get_assistant_llm] = lambda: UnavailableLLM("sin clave")
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    send(client, "hola")
    send(client, "ACEPTO")
    replies = send(client, "¿qué opinas del clima?").json()["replies"]
    assert any("ESTADO" in reply for reply in replies)
