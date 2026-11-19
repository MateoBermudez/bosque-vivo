import base64

from bosquevivo.ai.llm import LLMResponse, ScriptedLLM, UnavailableLLM
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


def post(client, **body):
    return client.post(
        "/api/v1/community/messages", headers=ADMIN, json={"session_ref": REF, **body}
    )


def onboard(client):
    send(client, "hola")
    send(client, "ACEPTO")


def test_location_from_the_browser_registers_the_project(client, db, seeded):
    client.app.dependency_overrides[get_assistant_llm] = lambda: ScriptedLLM([])
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    onboard(client)
    replies = post(client, kind="location", latitude=5.05, longitude=-74.95).json()["replies"]
    assert any("Reserva El Roble" in reply for reply in replies)
    assert db.query(WaUser).one().project_id == seeded.id


def test_photo_needs_separate_consent_and_reaches_the_model(client, db, seeded):
    llm = ScriptedLLM([LLMResponse(text="En la foto se ve bosque. Es evidencia no verificada.")])
    client.app.dependency_overrides[get_assistant_llm] = lambda: llm
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    onboard(client)
    photo = {
        "kind": "image",
        "mime_type": "image/jpeg",
        "media_base64": base64.b64encode(b"jpeg").decode(),
    }
    assert "ACEPTO FOTOS" in post(client, **photo).json()["replies"][0]
    assert llm.calls == []
    send(client, "ACEPTO FOTOS")
    replies = post(client, **photo, message="mi finca").json()["replies"]
    assert "foto" in replies[0]
    sent = llm.calls[0]["messages"][0]
    assert sent.media[0].mime_type == "image/jpeg" and sent.media[0].data == b"jpeg"


def test_voice_note_is_transcribed_then_answered(client, db, seeded):
    script = [LLMResponse(text="cómo está el bosque"), LLMResponse(text="Todavía no tengo datos.")]
    llm = ScriptedLLM(script)
    client.app.dependency_overrides[get_assistant_llm] = lambda: llm
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    onboard(client)
    send(client, "ACEPTO FOTOS")
    audio = base64.b64encode(b"RIFF....WAVE").decode()
    replies = post(client, kind="audio", mime_type="audio/wav", media_base64=audio).json()
    assert replies["replies"]
    assert llm.calls[0]["messages"][0].media[0].mime_type == "audio/wav"


def test_rejects_invalid_media_and_location(client):
    bad_type = {"kind": "image", "mime_type": "application/pdf", "media_base64": "eA=="}
    assert post(client, **bad_type).status_code == 422
    assert post(client, kind="image", mime_type="image/png", media_base64="%%%").status_code == 422
    assert post(client, kind="location", latitude=95, longitude=0).status_code == 422
    assert post(client, kind="text", message="  ").status_code == 422
