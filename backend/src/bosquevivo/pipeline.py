"""Calcula auditorías de uno o varios proyectos (comandos `audit` y `audit-batch`)."""

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.audit.service import AuditService, analysis_window_start
from bosquevivo.core.errors import NotFoundError
from bosquevivo.core.logging import get_logger
from bosquevivo.db.models import AuditResult, AuditRun, Project, Report
from bosquevivo.reports.service import ReportService
from bosquevivo.satellite.provider import SatelliteProvider
from bosquevivo.satellite.service import SatelliteService

log = get_logger(__name__)

# El índice v0 mide la permanencia de bosque que ya existía: no cubre reforestación (ARR).
SUPPORTED_KINDS = frozenset({"AD", "IFM"})


def project_kind(project_type: str | None) -> str | None:
    """«Deforestación evitada (AD)» → «AD»."""
    match = re.search(r"\((AD|ARR|IFM)\)\s*$", project_type or "")
    return match.group(1) if match else None


def audit_project(
    session: Session,
    provider: SatelliteProvider,
    images_dir: Path,
    project_id: int,
    *,
    start: date | None = None,
) -> AuditRun:
    """Trae los datos satelitales del proyecto y calcula su índice."""
    audits = AuditService(session, dataset_versions=provider.dataset_versions())
    project = session.get(Project, project_id)
    if project is None:
        raise NotFoundError(f"proyecto {project_id} no existe")
    window_start = start or analysis_window_start(audits.resolve_t0(project))
    satellite = SatelliteService(session, provider, images_dir)
    satellite.refresh_timeseries(project_id, window_start, date.today())
    satellite.refresh_forest_loss(project_id)
    return audits.run(project_id)


def select_projects(
    session: Session,
    *,
    country: str | None = None,
    include_arr: bool = False,
    max_area_ha: float | None = None,
    redo: bool = False,
    missing_index: bool = False,
    limit: int | None = None,
    shard: tuple[int, int] | None = None,
) -> list[Project]:
    """Proyectos a calcular, de menor a mayor área (los chicos terminan primero).

    `shard=(i, n)` reparte la lista entre n procesos y devuelve la parte i (0 a n-1).
    `missing_index=True` incluye los que no tienen una corrida con puntaje (sin auditoría o con
    resultado parcial), aunque ya tengan una corrida terminada."""
    stmt = select(Project).where(Project.source_registry != "demo").order_by(Project.area_ha)
    if country:
        stmt = stmt.where(Project.country == country)
    if max_area_ha is not None:
        stmt = stmt.where(Project.area_ha <= max_area_ha)
    done = set(session.scalars(select(AuditRun.project_id).where(AuditRun.status == "done")))
    scored = set(
        session.scalars(
            select(AuditRun.project_id)
            .join(AuditResult, AuditResult.run_id == AuditRun.id)
            .where(AuditRun.status == "done", AuditResult.score.is_not(None))
        )
    )
    selected: list[Project] = []
    for project in session.scalars(stmt):
        kind = project_kind(project.project_type)
        if kind == "ARR" and not include_arr:
            continue
        if kind is not None and kind not in SUPPORTED_KINDS | {"ARR"}:
            continue
        if missing_index:
            if project.id in scored and not redo:
                continue
        elif project.id in done and not redo:
            continue
        selected.append(project)
    if shard is not None:
        index, count = shard
        selected = selected[index::count]
    return selected[:limit] if limit is not None else selected


@dataclass
class BatchItem:
    project_id: int
    name: str
    area_ha: float | None
    ok: bool
    category: str | None = None
    score: float | None = None
    seconds: float = 0.0
    error: str | None = None


def run_batch(
    session: Session,
    provider: SatelliteProvider,
    images_dir: Path,
    projects: list[Project],
    *,
    start: date | None = None,
    reports_dir: Path | None = None,
    on_item: Callable[[int, int, BatchItem], None] | None = None,
) -> list[BatchItem]:
    """Calcula cada proyecto por separado; un fallo no frena el lote."""
    items: list[BatchItem] = []
    for index, project in enumerate(projects, start=1):
        began = time.monotonic()
        item = BatchItem(project.id, project.name, project.area_ha, ok=False)
        try:
            run = audit_project(session, provider, images_dir, project.id, start=start)
            session.commit()
            item.ok = True
            if reports_dir is not None:
                _try_report(session, reports_dir, run.id)
            item.category = run.result.category if run.result else None
            item.score = run.result.score if run.result else None
        except Exception as exc:  # un proyecto con problemas no debe frenar el lote
            session.rollback()
            item.error = f"{type(exc).__name__}: {exc}"
            log.warning("batch_item_failed", project_id=project.id, error=item.error)
        item.seconds = round(time.monotonic() - began, 1)
        items.append(item)
        if on_item:
            on_item(index, len(projects), item)
    return items


def _try_report(session: Session, reports_dir: Path, run_id: int) -> bool:
    """Genera el reporte HTML de una corrida; si falla se registra y el lote sigue."""
    try:
        ReportService(session, reports_dir).generate(run_id, "html")
        session.commit()
        return True
    except (
        Exception
    ) as exc:  # el reporte es un extra: no debe hacer fallar una auditoría ya guardada
        session.rollback()
        log.warning("report_failed", run_id=run_id, error=str(exc))
        return False


def generate_missing_reports(session: Session, reports_dir: Path) -> int:
    """Genera el reporte HTML de la última corrida terminada de cada proyecto que no lo tenga."""
    have = set(session.scalars(select(Report.run_id).where(Report.format == "html")))
    latest: dict[int, int] = {}
    for run in session.scalars(
        select(AuditRun).where(AuditRun.status == "done").order_by(AuditRun.id)
    ):
        latest[run.project_id] = run.id
    created = 0
    for run_id in latest.values():
        if run_id not in have and _try_report(session, reports_dir, run_id):
            created += 1
    return created
