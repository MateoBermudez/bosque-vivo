from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from bosquevivo.assistant.messages import IncomingMessage
from bosquevivo.assistant.runtime import build_assistant, build_llm
from bosquevivo.audit.index import IndexCalculator
from bosquevivo.audit.service import AuditService, analysis_window_start
from bosquevivo.core.config import get_settings
from bosquevivo.db.models import Project
from bosquevivo.jobs.kinds import CALCULATE_AUDIT, GENERATE_REPORT, WHATSAPP_MESSAGE
from bosquevivo.reports.service import ReportService
from bosquevivo.satellite.provider import SatelliteProvider
from bosquevivo.satellite.service import SatelliteService

__all__ = ["CALCULATE_AUDIT", "GENERATE_REPORT", "WHATSAPP_MESSAGE"]


def make_calculate_audit(provider: SatelliteProvider):
    def handler(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = int(payload["project_id"])
        settings = get_settings()
        satellite = SatelliteService(session, provider, settings.images_dir)
        audit = AuditService(session, IndexCalculator(), provider.dataset_versions())
        project = session.get(Project, project_id)
        if payload.get("start"):
            start = date.fromisoformat(payload["start"])
        else:
            start = analysis_window_start(audit.resolve_t0(project) if project else None)
        end = date.fromisoformat(payload["end"]) if payload.get("end") else date.today()
        satellite.refresh_timeseries(project_id, start, end)
        satellite.refresh_forest_loss(project_id)
        run = audit.run(project_id)
        return {"run_id": run.id}

    return handler


def generate_report(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    service = ReportService(session, get_settings().reports_dir)
    report = service.generate(int(payload["run_id"]), payload.get("format", "html"))
    return {"report_id": report.id, "path": report.path}


def make_whatsapp_message(provider: SatelliteProvider | None):
    def handler(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
        llm = build_llm(settings)
        assistant = build_assistant(session, settings, llm, satellite_provider=provider)
        assistant.handle(IncomingMessage(**payload))
        return {"message_id": payload["message_id"]}

    return handler
