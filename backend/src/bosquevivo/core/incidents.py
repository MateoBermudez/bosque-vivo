from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.core.logging import get_logger
from bosquevivo.db.base import utcnow
from bosquevivo.db.models import Incident

log = get_logger(__name__)

Origin = Literal["externo", "interno"]

CRITICAL_MINUTES = 60


def classify(error: BaseException) -> Origin:
    return "externo" if isinstance(error, ExternalServiceError) else "interno"


def as_aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def record_incident(
    session: Session,
    component: str,
    error: BaseException | str,
    *,
    origin: Origin | None = None,
    severity: str = "error",
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> Incident:
    resolved_origin = origin or (classify(error) if isinstance(error, BaseException) else "interno")
    cause = str(error)[:2000] or type(error).__name__
    incident = Incident(
        component=component,
        origin=resolved_origin,
        severity=severity,
        cause=cause,
        started_at=started_at or utcnow(),
        ended_at=ended_at,
    )
    session.add(incident)
    session.flush()
    log.warning(
        "incident_recorded",
        component=component,
        origin=resolved_origin,
        severity=severity,
        incident_id=incident.id,
    )
    return incident


@contextmanager
def tracked(session: Session, component: str) -> Iterator[None]:
    began = utcnow()
    try:
        yield
    except Exception as exc:
        record_incident(session, component, exc, started_at=began, ended_at=utcnow())
        raise


def close_incident(session: Session, incident_id: int, ended_at: datetime | None = None) -> None:
    incident = session.get(Incident, incident_id)
    if incident and incident.ended_at is None:
        incident.ended_at = ended_at or utcnow()
        session.flush()


def list_incidents(session: Session, days: int = 30) -> list[Incident]:
    since = utcnow() - timedelta(days=days)
    rows = session.scalars(select(Incident).order_by(Incident.started_at.desc())).all()
    return [row for row in rows if as_aware(row.started_at) >= since]


def duration_minutes(incident: Incident) -> float | None:
    if incident.ended_at is None:
        return None
    delta = as_aware(incident.ended_at) - as_aware(incident.started_at)
    return round(delta.total_seconds() / 60, 2)


def is_critical(incident: Incident) -> bool:
    minutes = duration_minutes(incident)
    return incident.severity == "critico" or (minutes is not None and minutes > CRITICAL_MINUTES)


def summarize(incidents: list[Incident]) -> dict[str, int]:
    return {
        "total": len(incidents),
        "externos": sum(1 for i in incidents if i.origin == "externo"),
        "internos": sum(1 for i in incidents if i.origin == "interno"),
        "criticos": sum(1 for i in incidents if is_critical(i)),
        "abiertos": sum(1 for i in incidents if i.ended_at is None),
    }
