from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bosquevivo.api.deps import db_session, require_admin
from bosquevivo.api.schemas import ImportOut, ImportRequest

router = APIRouter(
    prefix="/api/v1/admin", tags=["administración"], dependencies=[Depends(require_admin)]
)


@router.post("/import", response_model=ImportOut)
def import_projects(body: ImportRequest, session: Session = Depends(db_session)):
    try:
        from bosquevivo.registry.importer import import_file
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="La importación de archivos necesita las dependencias de procesamiento; "
            "use la CLI (bosquevivo import) desde un equipo.",
        ) from exc
    summary = import_file(
        session,
        Path(body.path),
        source=body.source,
        source_version=body.source_version,
        country=body.country,
        limit=body.limit,
        strict=body.strict,
    )
    return ImportOut(
        created=summary.created,
        updated=summary.updated,
        repaired=summary.repaired,
        skipped=summary.skipped,
        rejected=summary.rejected,
        created_ids=summary.created_ids,
        errors=summary.errors,
    )
