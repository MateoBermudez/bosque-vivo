from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from bosquevivo.api.deps import db_session, require_admin
from bosquevivo.api.schemas import ImportOut, ImportRequest
from bosquevivo.registry.importer import import_file

router = APIRouter(
    prefix="/api/v1/admin", tags=["administración"], dependencies=[Depends(require_admin)]
)


@router.post("/import", response_model=ImportOut)
def import_projects(body: ImportRequest, session: Session = Depends(db_session)):
    summary = import_file(
        session,
        Path(body.path),
        source=body.source,
        source_version=body.source_version,
        country=body.country,
        limit=body.limit,
    )
    return ImportOut(
        created=summary.created,
        updated=summary.updated,
        repaired=summary.repaired,
        skipped=summary.skipped,
    )
