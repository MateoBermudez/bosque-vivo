from typing import Protocol

import httpx

from bosquevivo.core.errors import ExternalServiceError

GRAPH_URL = "https://graph.facebook.com/v21.0"


class WhatsAppClient(Protocol):
    def send_text(self, to: str, body: str) -> None: ...

    def download_media(self, media_id: str) -> tuple[bytes, str]: ...


class CloudApiClient:
    def __init__(self, token: str, phone_number_id: str, timeout: float = 30.0) -> None:
        if not token or not phone_number_id:
            raise ExternalServiceError("WHATSAPP_TOKEN y WHATSAPP_PHONE_NUMBER_ID son obligatorios")
        self.phone_number_id = phone_number_id
        self.http = httpx.Client(
            headers={"Authorization": f"Bearer {token}"}, timeout=timeout, follow_redirects=True
        )

    def send_text(self, to: str, body: str) -> None:
        response = self.http.post(
            f"{GRAPH_URL}/{self.phone_number_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            },
        )
        if response.status_code >= 400:
            raise ExternalServiceError(f"error al enviar mensaje: {response.status_code}")

    def download_media(self, media_id: str) -> tuple[bytes, str]:
        meta = self.http.get(f"{GRAPH_URL}/{media_id}")
        if meta.status_code >= 400:
            raise ExternalServiceError(f"no se pudo obtener el archivo: {meta.status_code}")
        info = meta.json()
        content = self.http.get(info["url"])
        if content.status_code >= 400:
            raise ExternalServiceError(f"no se pudo descargar el archivo: {content.status_code}")
        return content.content, info.get("mime_type", "application/octet-stream")


class RecordingClient:
    def __init__(self, media: dict[str, tuple[bytes, str]] | None = None) -> None:
        self.sent: list[tuple[str, str]] = []
        self.media = media or {}

    def send_text(self, to: str, body: str) -> None:
        self.sent.append((to, body))

    def download_media(self, media_id: str) -> tuple[bytes, str]:
        return self.media[media_id]
