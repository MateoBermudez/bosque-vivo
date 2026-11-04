import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
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


class CommunityIn(BaseModel):
    session_ref: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9-]+$")
    message: str = Field(min_length=1, max_length=1000)


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
    client = RecordingClient()
    web_settings = settings.model_copy(update={"whatsapp_allowed_phones": ""})
    assistant = build_assistant(session, web_settings, llm, client, provider)
    assistant.handle(
        IncomingMessage(
            message_id=f"web-{uuid.uuid4().hex}",
            phone=f"web-{body.session_ref}",
            kind="text",
            text=body.message,
        )
    )
    return CommunityOut(replies=[text for _, text in client.sent])
