import statistics
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.ai.llm import LLMProvider
from bosquevivo.assistant import IncomingMessage
from bosquevivo.assistant.client import RecordingClient
from bosquevivo.assistant.runtime import build_assistant
from bosquevivo.audit import AuditService
from bosquevivo.audit.config import config_for
from bosquevivo.audit.index import IndexCalculator
from bosquevivo.core.config import Settings
from bosquevivo.db.models import Project
from bosquevivo.pipeline import audit_project
from bosquevivo.satellite.provider import SatelliteProvider

CHAT_LIMIT_SECONDS = 10.0
CHAT_TARGET_SHARE = 0.90
AUDIT_LIMIT_SECONDS = 300.0
MEASURE_PHONE = "000000000000"
QUESTIONS = (
    "estado",
    "alertas",
    "ayuda",
    "¿cómo está el bosque de mi finca?",
    "¿qué significa el índice de credibilidad?",
)


@dataclass
class Summary:
    samples: int
    p50: float
    p90: float
    maximum: float
    share_within_limit: float
    limit_seconds: float
    meets_target: bool


@dataclass
class Report:
    llm_model: str
    satellite_provider: str
    chat: Summary | None = None
    audit: Summary | None = None
    audit_by_project: dict[int, float] = field(default_factory=dict)
    deterministic: bool | None = None
    determinism_detail: dict[int, list[float | None]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def summarize(values: list[float], limit: float, target: float) -> Summary:
    ordered = sorted(values)
    within = sum(1 for value in ordered if value < limit) / len(ordered)
    p90_index = max(0, round(0.9 * len(ordered)) - 1)
    return Summary(
        samples=len(ordered),
        p50=round(statistics.median(ordered), 3),
        p90=round(ordered[p90_index], 3),
        maximum=round(ordered[-1], 3),
        share_within_limit=round(within, 3),
        limit_seconds=limit,
        meets_target=within >= target,
    )


def measure_chat(
    session: Session,
    settings: Settings,
    llm: LLMProvider,
    project_id: int | None,
    rounds: int,
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> Summary:
    client = RecordingClient()
    web_settings = settings.model_copy(update={"whatsapp_allowed_phones": ""})
    assistant = build_assistant(session, web_settings, llm, client)
    counter = iter(range(1_000_000))

    def say(text: str) -> float:
        began = clock()
        assistant.handle(
            IncomingMessage(
                message_id=f"medicion-{next(counter)}-{time.time_ns()}",
                phone=MEASURE_PHONE,
                kind="text",
                text=text,
            )
        )
        return clock() - began

    say("hola")
    say("ACEPTO")
    if project_id is not None:
        say(f"proyecto {project_id}")
    durations = [say(QUESTIONS[i % len(QUESTIONS)]) for i in range(rounds)]
    assistant.delete_user(MEASURE_PHONE)
    return summarize(durations, CHAT_LIMIT_SECONDS, CHAT_TARGET_SHARE)


def measure_audits(
    session: Session,
    provider: SatelliteProvider,
    images_dir: Path,
    project_ids: list[int],
    index_version: str,
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> tuple[Summary, dict[int, float]]:
    durations: dict[int, float] = {}
    for project_id in project_ids:
        began = clock()
        audit_project(session, provider, images_dir, project_id, index_version=index_version)
        durations[project_id] = round(clock() - began, 3)
    return summarize(list(durations.values()), AUDIT_LIMIT_SECONDS, 1.0), durations


def check_determinism(
    session: Session, project_ids: list[int], index_version: str
) -> tuple[bool, dict[int, list[float | None]]]:
    detail: dict[int, list[float | None]] = {}
    for project_id in project_ids:
        scores: list[float | None] = []
        for _ in range(2):
            service = AuditService(session, IndexCalculator(config_for(index_version)))
            run = service.run(project_id)
            scores.append(run.result.score if run.result else None)
        detail[project_id] = scores
    return all(len(set(values)) == 1 for values in detail.values()), detail


def project_ids(session: Session, limit: int) -> list[int]:
    return list(session.scalars(select(Project.id).order_by(Project.id).limit(limit)).all())
