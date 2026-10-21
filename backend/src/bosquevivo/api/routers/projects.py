import json
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.api.deps import db_session
from bosquevivo.api.schemas import LossOut, ProjectOut, SeriesOut, SeriesPointOut
from bosquevivo.audit.compare import compare_declared_observed
from bosquevivo.audit.service import AuditService
from bosquevivo.db.models import ForestLoss, NdviObservation
from bosquevivo.registry.repository import ProjectRepository

router = APIRouter(prefix="/api/v1/projects", tags=["proyectos"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    country: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(db_session),
):
    return ProjectRepository(session).list_projects(country, limit, offset)


@router.get("/locate", response_model=ProjectOut)
def locate(lat: float, lon: float, session: Session = Depends(db_session)):
    project = ProjectRepository(session).locate(lat, lon)
    if project is None:
        raise HTTPException(status_code=404, detail="ningún proyecto contiene ese punto")
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, session: Session = Depends(db_session)):
    project = ProjectRepository(session).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    return project


@router.get("/{project_id}/geometry")
def get_geometry(project_id: int, session: Session = Depends(db_session)):
    project = ProjectRepository(session).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    return {
        "type": "Feature",
        "properties": {"id": project.id, "name": project.name},
        "geometry": json.loads(project.geometry),
    }


@router.get("/{project_id}/series", response_model=SeriesOut)
def get_series(project_id: int, session: Session = Depends(db_session)):
    project = ProjectRepository(session).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="proyecto no encontrado")
    observations = session.scalars(
        select(NdviObservation)
        .where(NdviObservation.project_id == project_id)
        .order_by(NdviObservation.period)
    ).all()
    losses = session.scalars(
        select(ForestLoss).where(ForestLoss.project_id == project_id).order_by(ForestLoss.year)
    ).all()
    inputs = AuditService(session).build_inputs(project)
    return SeriesOut(
        t0=inputs.t0.isoformat() if inputs.t0 else None,
        ndvi=[
            SeriesPointOut(
                period=o.period.isoformat(),
                sensor=o.sensor,
                ndvi_mean=o.ndvi_mean,
                valid_fraction=o.valid_fraction,
                scene_count=o.scene_count,
            )
            for o in observations
        ],
        loss=[LossOut(year=r.year, ha_lost=r.ha_lost) for r in losses],
        comparison=[asdict(row) for row in compare_declared_observed(inputs)],
    )
