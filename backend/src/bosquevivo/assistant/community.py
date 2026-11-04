from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.db.models import AuditResult, AuditRun, ForestBaselineRecord, ForestLoss, Project

ALERT_RATE_PCT = 0.5
RECENT_YEARS = 3

CATEGORY_TEXT = {
    "alta": "lo que se ve desde el satélite coincide bien con lo que el proyecto declara",
    "media": "lo que se ve desde el satélite coincide solo en parte con lo que el proyecto declara",
    "baja": "lo que se ve desde el satélite coincide poco con lo que el proyecto declara",
}


def latest_result(session: Session, project_id: int) -> AuditResult | None:
    run = session.scalars(
        select(AuditRun)
        .where(AuditRun.project_id == project_id, AuditRun.status == "done")
        .order_by(AuditRun.id.desc())
    ).first()
    return run.result if run else None


def _permanence_pct(result: AuditResult) -> float | None:
    component = (result.components or {}).get("permanencia")
    if not isinstance(component, dict):
        return None
    value = component.get("porcentaje_en_pie")
    return float(value) if isinstance(value, int | float) else None


def _short(name: str) -> str:
    return name if len(name) <= 60 else name[:57] + "..."


def _pct(value: float) -> str:
    return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}".replace(".", ",")


def status_message(session: Session, project: Project) -> str:
    result = latest_result(session, project.id)
    name = _short(project.name)
    if result is None:
        return (
            f"Todavía no hemos revisado {name} con imágenes de satélite. "
            "Escriba AYUDA para ver otras consultas."
        )
    since = f" desde {project.start_year}" if project.start_year else ""
    kept = _permanence_pct(result)
    parts: list[str] = []
    if kept is not None:
        parts.append(f"En {name} se conserva el {_pct(kept)} % del bosque que había{since}.")
    category = (result.category or "").lower()
    if category in CATEGORY_TEXT:
        parts.append(f"En general, {CATEGORY_TEXT[category]}.")
    else:
        parts.append(f"Aún no hay datos suficientes para dar un resultado completo de {name}.")
    if result.confidence_label == "baja":
        parts.append("Ojo: hay pocas imágenes claras, así que el resultado es poco seguro.")
    parts.append("Escriba ALERTAS para ver cambios recientes.")
    return " ".join(parts)


def _losses(session: Session, project_id: int) -> dict[int, float]:
    rows = session.scalars(select(ForestLoss).where(ForestLoss.project_id == project_id)).all()
    totals: dict[int, float] = {}
    for row in rows:
        totals[row.year] = totals.get(row.year, 0.0) + row.ha_lost
    return totals


def _baseline(session: Session, project_id: int) -> float | None:
    record = session.scalars(
        select(ForestBaselineRecord).where(ForestBaselineRecord.project_id == project_id)
    ).first()
    return record.tree_cover_ha if record and record.tree_cover_ha > 0 else None


def project_alerts(session: Session, project: Project) -> list[tuple[int, float, float]]:
    losses = _losses(session, project.id)
    baseline = _baseline(session, project.id)
    if not losses or baseline is None:
        return []
    years = sorted(losses)[-RECENT_YEARS:]
    alerts: list[tuple[int, float, float]] = []
    for year in years:
        rate = losses[year] / baseline * 100
        if rate >= ALERT_RATE_PCT:
            alerts.append((year, losses[year], rate))
    return alerts


def alerts_message(session: Session, project: Project) -> str:
    name = _short(project.name)
    losses = _losses(session, project.id)
    if _baseline(session, project.id) is None:
        return f"Todavía no tenemos datos de pérdida de bosque para {name}."
    if not losses:
        return f"Sin alertas para {name}: no se detectó pérdida de bosque en su área."
    alerts = project_alerts(session, project)
    last = max(losses)
    if not alerts:
        return (
            f"Sin alertas para {name}: hasta {last} la pérdida de bosque fue baja "
            f"(menos del {_pct(ALERT_RATE_PCT)} % por año)."
        )
    items = "; ".join(
        f"en {year} se perdieron {ha:.0f} ha ({_pct(rate)} %)" for year, ha, rate in alerts
    )
    return (
        f"Alerta para {name}: {items} del bosque. Es lo que se ve desde el satélite; "
        "no dice quién ni por qué."
    )
