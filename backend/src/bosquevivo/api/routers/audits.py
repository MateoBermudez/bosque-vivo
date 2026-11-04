from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bosquevivo.api.deps import db_session, require_admin
from bosquevivo.api.routers.projects import light_geometry
from bosquevivo.api.schemas import AuditRunOut, ExplorerItemOut, JobOut, ProjectOut
from bosquevivo.audit.service import AuditService
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.core.errors import NotFoundError
from bosquevivo.db.models import AuditRun, Project, Report
from bosquevivo.jobs.dispatch import submit
from bosquevivo.jobs.kinds import CALCULATE_AUDIT, GENERATE_REPORT
from bosquevivo.jobs.queue import JobQueue

router = APIRouter(prefix="/api/v1", tags=["auditorías"])


@router.get("/projects/{project_id}/audit", response_model=AuditRunOut)
def latest_audit(project_id: int, session: Session = Depends(db_session)):
    run = AuditService(session).latest(project_id)
    if run is None:
        raise HTTPException(status_code=404, detail="el proyecto no tiene auditorías")
    return run


@router.post(
    "/projects/{project_id}/audit", response_model=JobOut, dependencies=[Depends(require_admin)]
)
def request_audit(
    project_id: int,
    session: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
):
    if session.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    return submit(session, settings, CALCULATE_AUDIT, {"project_id": project_id})


@router.post(
    "/audits/{run_id}/report", response_model=JobOut, dependencies=[Depends(require_admin)]
)
def request_report(
    run_id: int,
    format: str = "html",
    session: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
):
    if format not in {"html", "pdf"}:
        raise HTTPException(status_code=422, detail="formato no soportado")
    if session.get(AuditRun, run_id) is None:
        raise HTTPException(status_code=404, detail="corrida no encontrada")
    return submit(session, settings, GENERATE_REPORT, {"run_id": run_id, "format": format})


@router.get("/audits/{run_id}/report")
def download_report(
    run_id: int,
    format: str = "html",
    session: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
):
    if format not in {"html", "pdf"}:
        raise HTTPException(status_code=422, detail="formato no soportado")
    report = (
        session.query(Report)
        .filter(Report.run_id == run_id, Report.format == format)
        .order_by(Report.id.desc())
        .first()
    )
    if report is None or not Path(report.path).exists():
        from bosquevivo.reports.service import ReportService

        try:
            report = ReportService(session, settings.reports_dir).generate(run_id, format)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    media = "application/pdf" if format == "pdf" else "text/html"
    return FileResponse(report.path, media_type=media)


@router.get("/jobs/{job_id}", response_model=JobOut)
def job_status(job_id: int, session: Session = Depends(db_session)):
    job = JobQueue(session).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="trabajo no encontrado")
    return job


@router.get("/explorer", response_model=list[ExplorerItemOut])
def explorer(
    simplify: float = Query(default=0.005, ge=0, le=0.1),
    max_parts: int = Query(default=200, ge=1, le=100_000),
    session: Session = Depends(db_session),
):
    latest_ids = (
        select(func.max(AuditRun.id))
        .where(AuditRun.status == "done")
        .group_by(AuditRun.project_id)
        .scalar_subquery()
    )
    runs = {
        run.project_id: run
        for run in session.scalars(select(AuditRun).where(AuditRun.id.in_(latest_ids))).all()
    }
    items = []
    for project in session.scalars(select(Project).order_by(Project.name)).all():
        geometry = light_geometry(project.id, project.geometry, simplify, max_parts)
        run = runs.get(project.id)
        items.append(
            ExplorerItemOut(
                project=ProjectOut.model_validate(project),
                geometry={
                    "type": "Feature",
                    "properties": {"id": project.id, "name": project.name},
                    "geometry": geometry,
                },
                audit=AuditRunOut.model_validate(run, from_attributes=True) if run else None,
            )
        )
    return items
