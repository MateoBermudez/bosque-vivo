from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from bosquevivo.core.config import Settings
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.core.incidents import record_incident
from bosquevivo.core.logging import get_logger
from bosquevivo.db.base import utcnow
from bosquevivo.db.models import Job
from bosquevivo.jobs.kinds import CALCULATE_AUDIT, GENERATE_REPORT, WHATSAPP_MESSAGE
from bosquevivo.jobs.queue import JobQueue
from bosquevivo.satellite.factory import build_provider
from bosquevivo.satellite.provider import SatelliteProvider

log = get_logger(__name__)

Handler = Callable[[Session, dict[str, Any]], dict[str, Any] | None]


def optional_provider(settings: Settings) -> SatelliteProvider | None:
    try:
        return build_provider(settings)
    except Exception as exc:
        log.warning("satellite_provider_unavailable", error=str(exc))
        return None


def build_handlers(provider: SatelliteProvider | None) -> dict[str, Handler]:
    from bosquevivo.jobs.tasks import (
        generate_report,
        make_calculate_audit,
        make_whatsapp_message,
    )

    handlers: dict[str, Handler] = {
        GENERATE_REPORT: generate_report,
        WHATSAPP_MESSAGE: make_whatsapp_message(provider),
    }
    if provider is not None:
        handlers[CALCULATE_AUDIT] = make_calculate_audit(provider)
    return handlers


def run_now(session: Session, job: Job, settings: Settings) -> Job:
    queue = JobQueue(session)
    provider = optional_provider(settings) if job.kind == CALCULATE_AUDIT else None
    handler = build_handlers(provider).get(job.kind)
    job.status = "running"
    job.attempts += 1
    session.commit()
    if handler is None:
        error = ExternalServiceError(
            "el cálculo satelital no está disponible en este servidor; ejecútelo con la CLI "
            "(bosquevivo audit) desde un equipo con las dependencias de procesamiento"
        )
        job.status = "failed"
        job.error = str(error)
        record_incident(session, f"tarea:{job.kind}", error, ended_at=utcnow())
        session.commit()
        return job
    try:
        queue.complete(job, handler(session, job.payload))
    except Exception as exc:
        session.rollback()
        failed = queue.get(job.id) or job
        failed.status = "failed"
        failed.error = str(exc)
        record_incident(session, f"tarea:{job.kind}", exc, ended_at=utcnow())
        log.error("job_failed", kind=job.kind, job_id=job.id, error=str(exc))
        session.commit()
        return failed
    session.commit()
    return job


def submit(session: Session, settings: Settings, kind: str, payload: dict[str, Any]) -> Job:
    job = JobQueue(session).enqueue(kind, payload)
    if settings.inline_jobs:
        return run_now(session, job, settings)
    return job
