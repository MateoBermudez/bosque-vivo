from dataclasses import dataclass
from typing import Any, Literal

Kind = Literal["text", "location", "image", "audio", "other"]


@dataclass(frozen=True)
class IncomingMessage:
    message_id: str
    phone: str
    kind: Kind
    text: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    media_id: str | None = None
    mime_type: str | None = None


def _parse_one(raw: dict[str, Any]) -> IncomingMessage:
    kind = raw.get("type", "other")
    base = {"message_id": raw.get("id", ""), "phone": raw.get("from", "")}
    if kind == "text":
        return IncomingMessage(**base, kind="text", text=raw.get("text", {}).get("body", ""))
    if kind == "location":
        loc = raw.get("location", {})
        return IncomingMessage(
            **base, kind="location", latitude=loc.get("latitude"), longitude=loc.get("longitude")
        )
    if kind in {"image", "audio"}:
        media = raw.get(kind, {})
        return IncomingMessage(
            **base,
            kind=kind,
            text=media.get("caption"),
            media_id=media.get("id"),
            mime_type=media.get("mime_type"),
        )
    return IncomingMessage(**base, kind="other")


def parse_webhook(payload: dict[str, Any]) -> list[IncomingMessage]:
    messages: list[IncomingMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for raw in change.get("value", {}).get("messages", []):
                parsed = _parse_one(raw)
                if parsed.message_id and parsed.phone:
                    messages.append(parsed)
    return messages
