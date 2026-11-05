from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from bosquevivo.accounts import AccountService, build_mailer
from bosquevivo.api.deps import db_session, require_admin
from bosquevivo.api.schemas import ImportOut, ImportRequest
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.core.errors import ExternalServiceError, ValidationFailedError
from bosquevivo.core.incidents import duration_minutes, is_critical, list_incidents, summarize
from bosquevivo.db.remote import (
    CLEAR_CONFIRMATION,
    clear_all,
    finish_restore,
    restore_rows,
    table_counts,
)

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


class RestoreIn(BaseModel):
    table: str
    rows: list[dict[str, Any]]


class ClearIn(BaseModel):
    confirm: str


@router.get("/restore")
def restore_status(session: Session = Depends(db_session)):
    return {"counts": table_counts(session)}


@router.post("/restore")
def restore(body: RestoreIn, session: Session = Depends(db_session)):
    try:
        inserted = restore_rows(session, body.table, body.rows)
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"tabla desconocida: {body.table}") from exc
    return {"table": body.table, "inserted": inserted}


@router.post("/restore/clear")
def restore_clear(body: ClearIn, session: Session = Depends(db_session)):
    if body.confirm != CLEAR_CONFIRMATION:
        raise HTTPException(
            status_code=422, detail=f'escriba "{CLEAR_CONFIRMATION}" para confirmar'
        )
    clear_all(session)
    return {"counts": table_counts(session)}


@router.post("/restore/finish")
def restore_finish(session: Session = Depends(db_session)):
    return {"counts": finish_restore(session)}


class InviteIn(BaseModel):
    email: str
    name: str = ""


@router.get("/incidents")
def incidents(days: int = 30, limit: int = 50, session: Session = Depends(db_session)):
    rows = list_incidents(session, days=max(1, min(days, 365)))
    return {
        "summary": summarize(rows),
        "incidents": [
            {
                "id": row.id,
                "component": row.component,
                "origin": row.origin,
                "severity": row.severity,
                "critical": is_critical(row),
                "cause": row.cause,
                "started_at": row.started_at.isoformat(),
                "minutes": duration_minutes(row),
            }
            for row in rows[: max(1, min(limit, 500))]
        ],
    }


@router.get("/users")
def list_users(session: Session = Depends(db_session), settings: Settings = Depends(get_settings)):
    users = AccountService(session, build_mailer(settings), settings).list_users()
    return [{"email": u.email, "name": u.name, "active": u.active} for u in users]


@router.post("/users/invite")
def invite_user(
    body: InviteIn,
    session: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
):
    mailer = build_mailer(settings)
    try:
        user, link = AccountService(session, mailer, settings).invite_user(body.email, body.name)
    except ValidationFailedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    emailed = mailer.name == "smtp"
    return {"email": user.email, "emailed": emailed, "link": None if emailed else link}


class MailTestIn(BaseModel):
    to: str


@router.post("/mail-test")
def mail_test(
    body: MailTestIn,
    session: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
):
    mailer = build_mailer(settings)
    try:
        AccountService(session, mailer, settings).send_test(body.to)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"backend": mailer.name, "to": body.to}
