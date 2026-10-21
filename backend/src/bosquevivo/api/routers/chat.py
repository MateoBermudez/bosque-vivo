from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.ai.agent import Agent, AgentRequest, default_registry
from bosquevivo.ai.llm import LLMProvider
from bosquevivo.api.deps import db_session, get_llm, get_satellite_provider, require_admin
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.db.models import AgentRun
from bosquevivo.satellite.provider import SatelliteProvider
from bosquevivo.satellite.service import SatelliteService

router = APIRouter(prefix="/api/v1", tags=["agente"], dependencies=[Depends(require_admin)])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_ref: str = Field(default="panel", max_length=60)


class ChatOut(BaseModel):
    answer: str
    evidence_ids: list[str]
    tools_called: list[str]
    used_fallback: bool
    query_class: str
    run_id: int


class TraceOut(BaseModel):
    id: int
    role: str
    query_class: str
    query: str
    answer: str | None
    model: str | None
    prompt_version: str
    used_fallback: bool
    validator_passed: bool | None
    latency_ms: int | None
    tools: list[str]


@router.post("/chat", response_model=ChatOut)
def chat(
    body: ChatIn,
    session: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
    llm: LLMProvider = Depends(get_llm),
    provider: SatelliteProvider | None = Depends(get_satellite_provider),
):
    satellite = SatelliteService(session, provider, settings.images_dir) if provider else None
    agent = Agent(session, llm, default_registry(), settings, satellite)
    answer = agent.answer(
        AgentRequest(text=body.message, role="auditor", user_ref=f"panel:{body.session_ref}")
    )
    return ChatOut(
        answer=answer.text,
        evidence_ids=answer.evidence_ids,
        tools_called=answer.tools_called,
        used_fallback=answer.used_fallback,
        query_class=answer.query_class,
        run_id=answer.run_id,
    )


@router.get("/traces", response_model=list[TraceOut])
def traces(limit: int = Query(default=50, ge=1, le=200), session: Session = Depends(db_session)):
    runs = session.scalars(select(AgentRun).order_by(AgentRun.id.desc()).limit(limit)).all()
    return [
        TraceOut(
            id=r.id,
            role=r.role,
            query_class=r.query_class,
            query=r.query,
            answer=r.answer,
            model=r.model,
            prompt_version=r.prompt_version,
            used_fallback=r.used_fallback,
            validator_passed=r.validator_passed,
            latency_ms=r.latency_ms,
            tools=[s.tool for s in r.steps],
        )
        for r in runs
    ]
