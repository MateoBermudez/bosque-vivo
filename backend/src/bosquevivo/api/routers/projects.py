from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from bosquevivo.api.deps import db_session
from bosquevivo.api.schemas import ProjectOut
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
