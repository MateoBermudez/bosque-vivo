import base64
import binascii
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from bosquevivo.ai.llm import LLMProvider
from bosquevivo.api.deps import (
    db_session,
    get_assistant_llm,
    get_satellite_provider,
    require_admin,
)
from bosquevivo.assistant import IncomingMessage
from bosquevivo.assistant.client import RecordingClient
from bosquevivo.assistant.runtime import build_assistant
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.satellite.provider import SatelliteProvider

router = APIRouter(
    prefix="/api/v1/community", tags=["chat comunitario"], dependencies=[Depends(require_admin)]
)


IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
AUDIO_TYPES = {"audio/wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/aac"}
MAX_MEDIA_BYTES = 3_000_000


class CommunityIn(BaseModel):
    """Mensaje del chat en línea: texto, ubicación del navegador, foto o nota de voz."""

    session_ref: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9-]+$")
    kind: Literal["text", "location", "image", "audio"] = "text"
    message: str | None = Field(default=None, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    media_base64: str | None = Field(default=None, max_length=MAX_MEDIA_BYTES * 4 // 3 + 4)
    mime_type: str | None = Field(default=None, max_length=60)

    @model_validator(mode="after")
    def _check_kind(self) -> "CommunityIn":
        if self.kind == "text" and not (self.message or "").strip():
            raise ValueError("escriba un mensaje")
        if self.kind == "location" and (self.latitude is None or self.longitude is None):
            raise ValueError("faltan la latitud y la longitud")
        if self.kind in {"image", "audio"}:
            allowed = IMAGE_TYPES if self.kind == "image" else AUDIO_TYPES
            mime = (self.mime_type or "").split(";")[0].strip().lower()
            if not self.media_base64 or mime not in allowed:
                raise ValueError("el archivo no es una foto o un audio admitido")
            self.mime_type = mime
        return self

    def media(self) -> bytes | None:
        if not self.media_base64:
            return None
        try:
            data = base64.b64decode(self.media_base64, validate=True)
        except (binascii.Error, ValueError):
            return None
        return data if 0 < len(data) <= MAX_MEDIA_BYTES else None


class CommunityOut(BaseModel):
    replies: list[str]


@router.post("/messages", response_model=CommunityOut)
def send_message(
    body: CommunityIn,
    session: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
    llm: LLMProvider = Depends(get_assistant_llm),
    provider: SatelliteProvider | None = Depends(get_satellite_provider),
):
    media_id = None
    stored: dict[str, tuple[bytes, str]] = {}
    if body.kind in {"image", "audio"}:
        data = body.media()
        if data is None:
            raise HTTPException(status_code=422, detail="El archivo está vacío o supera los 3 MB.")
        media_id = f"web-{uuid.uuid4().hex}"
        stored[media_id] = (data, body.mime_type or "")
    client = RecordingClient(stored)
    web_settings = settings.model_copy(update={"whatsapp_allowed_phones": ""})
    assistant = build_assistant(session, web_settings, llm, client, provider)
    assistant.handle(
        IncomingMessage(
            message_id=f"web-{uuid.uuid4().hex}",
            phone=f"web-{body.session_ref}",
            kind=body.kind,
            text=(body.message or "").strip() or None,
            latitude=body.latitude,
            longitude=body.longitude,
            media_id=media_id,
            mime_type=body.mime_type,
        )
    )
    return CommunityOut(replies=[text for _, text in client.sent])
