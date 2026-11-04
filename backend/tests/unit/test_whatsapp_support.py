import httpx
import pytest

from bosquevivo.assistant import parse_webhook, verify_signature
from bosquevivo.assistant.client import CloudApiClient
from bosquevivo.assistant.dialogue import (
    split_message,
    wants_consent,
    wants_deletion,
    wants_media_consent,
)
from bosquevivo.assistant.signature import compute_signature
from bosquevivo.core.errors import ExternalServiceError

SECRET = "app-secret"


def payload(*messages):
    return {"entry": [{"changes": [{"value": {"messages": list(messages)}}]}]}


def test_valid_signature_is_accepted():
    body = b'{"a":1}'
    assert verify_signature(body, compute_signature(body, SECRET), SECRET)


def test_tampered_body_or_missing_header_is_rejected():
    body = b'{"a":1}'
    header = compute_signature(body, SECRET)
    assert not verify_signature(b'{"a":2}', header, SECRET)
    assert not verify_signature(body, None, SECRET)
    assert not verify_signature(body, header, "")


def test_parse_text_location_and_media_messages():
    parsed = parse_webhook(
        payload(
            {"id": "m1", "from": "573001112233", "type": "text", "text": {"body": "hola"}},
            {
                "id": "m2",
                "from": "573001112233",
                "type": "location",
                "location": {"latitude": 5.1, "longitude": -75.2},
            },
            {
                "id": "m3",
                "from": "573001112233",
                "type": "audio",
                "audio": {"id": "a1", "mime_type": "audio/ogg"},
            },
            {"id": "m4", "from": "573001112233", "type": "sticker"},
        )
    )
    assert [m.kind for m in parsed] == ["text", "location", "audio", "other"]
    assert parsed[1].latitude == 5.1
    assert parsed[2].media_id == "a1"


def test_parse_ignores_status_updates():
    assert parse_webhook({"entry": [{"changes": [{"value": {"statuses": [{"id": "x"}]}}]}]}) == []


def test_consent_and_deletion_phrases():
    assert wants_consent("Acepto")
    assert wants_consent(" ACEPTO. ")
    assert not wants_consent("no acepto")
    assert wants_media_consent("acepto fotos")
    assert wants_deletion("Borrar mis datos")
    assert wants_deletion("quiero eliminar mis datos por favor")
    assert not wants_deletion("¿cómo están los datos del proyecto?")


def test_split_message_respects_limit_and_keeps_content():
    text = "Primera frase larga. " * 20
    chunks = split_message(text, 100)
    assert all(len(c) <= 100 for c in chunks)
    assert len(chunks) > 1
    assert split_message("corto") == ["corto"]


def test_cloud_api_uses_configured_version_and_reports_errors():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        if request.url.path.endswith("/messages") and b"573000000000" in request.content:
            return httpx.Response(400, json={"error": {"message": "recipient not allowed"}})
        return httpx.Response(200, json={"messages": [{"id": "wamid.1"}]})

    client = CloudApiClient("token", "123", base_url="https://graph.test/", version="v25.0")
    client.http = httpx.Client(transport=httpx.MockTransport(handler))
    client.send_text("573001112233", "hola")
    assert seen == ["https://graph.test/v25.0/123/messages"]
    with pytest.raises(ExternalServiceError, match="recipient not allowed"):
        client.send_text("573000000000", "hola")
