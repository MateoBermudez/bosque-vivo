from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.ai.agent.tools.portfolio import latest_results, portfolio_row
from bosquevivo.db.models import AuditResult, AuditRun, ForestBaselineRecord, ForestLoss, Project

PORTFOLIO_LEVELS = ("Alta", "Media", "Baja")
ALERT_RATE_PCT = 0.5
RECENT_YEARS = 3
STEADY_RATIO = 1.1

CATEGORY_TEXT = {
    "alta": "lo que se ve desde el satélite coincide bien con lo que el proyecto declara",
    "media": "lo que se ve desde el satélite coincide solo en parte con lo que el proyecto declara",
    "baja": "lo que se ve desde el satélite coincide poco con lo que el proyecto declara",
}

CONFIDENCE_TEXT = {
    "alta": (
        "La confianza es alta: hubo suficientes imágenes claras, así que el resultado es firme."
    ),
    "media": (
        "La confianza es media: hubo imágenes claras, pero no tantas; tómelo con algo de cuidado."
    ),
    "baja": (
        "La confianza es baja: hubo pocas imágenes claras (por las nubes, por ejemplo); tómelo "
        "con mucho cuidado y consulte a una persona del equipo."
    ),
}

COMPONENT_TEXT = {
    "permanencia": "cuánto bosque se pierde cada año",
    "evolucion_perdida": "si esa pérdida cambió desde que empezó el proyecto",
    "tendencia": "hacia dónde va el verdor de la vegetación",
    "estabilidad": "si hubo caídas bruscas del verdor",
}


@dataclass(frozen=True)
class ProjectCard:
    project_id: int
    name: str
    country: str | None
    area_ha: float | None
    score: float | None
    category: str | None
    confidence_label: str | None
    forest_standing_pct: float | None


def latest_result(session: Session, project_id: int) -> AuditResult | None:
    run = session.scalars(
        select(AuditRun)
        .where(AuditRun.project_id == project_id, AuditRun.status == "done")
        .order_by(AuditRun.id.desc())
    ).first()
    return run.result if run else None


def _component(result: AuditResult, name: str) -> dict:
    component = (result.components or {}).get(name)
    return component if isinstance(component, dict) else {}


def _permanence_pct(result: AuditResult) -> float | None:
    value = _component(result, "permanencia").get("porcentaje_en_pie")
    return float(value) if isinstance(value, int | float) else None


def _short(name: str) -> str:
    return name if len(name) <= 60 else name[:57] + "..."


def _pct(value: float) -> str:
    return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}".replace(".", ",")


def _ha(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _is_reforestation(project: Project) -> bool:
    return "(ARR)" in (project.project_type or "")


def _evolution_sentence(result: AuditResult) -> str | None:
    detail = _component(result, "evolucion_perdida")
    if detail.get("nota"):
        return "Casi no se ha perdido bosque, ni antes ni después de que empezara el proyecto."
    ratio = detail.get("cociente_despues_antes")
    before = detail.get("perdida_anual_antes_ha")
    after = detail.get("perdida_anual_despues_ha")
    if not (
        isinstance(ratio, int | float)
        and isinstance(before, int | float)
        and isinstance(after, int | float)
    ):
        return None
    if ratio <= STEADY_RATIO:
        return "La pérdida de bosque por año no ha aumentado desde que empezó el proyecto."
    return (
        f"La pérdida de bosque por año pasó de {_ha(before)} a {_ha(after)} hectáreas desde que "
        "empezó el proyecto; esto no dice por qué cambió."
    )


def _summary_sentence(result: AuditResult) -> str:
    category = (result.category or "").lower()
    if category not in CATEGORY_TEXT or result.score is None:
        return "Aún no hay datos suficientes para dar un resultado completo."
    confidence = f", confianza {result.confidence_label}" if result.confidence_label else ""
    return f"En general, {CATEGORY_TEXT[category]} (índice {result.score:.0f} de 100{confidence})."


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
    if kept is None and _is_reforestation(project):
        return (
            f"{name} es un proyecto de reforestación: el índice actual mide bosque que ya existía, "
            "por eso todavía no calculamos un resultado para él."
        )
    parts: list[str] = []
    if kept is not None:
        parts.append(f"En {name} se conserva el {_pct(kept)} % del bosque que había{since}.")
    evolution = _evolution_sentence(result)
    if evolution:
        parts.append(evolution)
    parts.append(_summary_sentence(result))
    if result.confidence_label == "baja":
        parts.append("Ojo: hay pocas imágenes claras, así que el resultado es poco seguro.")
    parts.append("Escriba ALERTAS para ver cambios recientes o pregúnteme lo que quiera.")
    return " ".join(parts)


def index_message(session: Session, project: Project) -> str:
    result = latest_result(session, project.id)
    name = _short(project.name)
    if result is None:
        return f"Todavía no hemos calculado el índice de {name}."
    if result.score is None:
        return (
            f"Todavía no hay un índice completo para {name}: faltan datos suficientes. "
            "Eso pasa, por ejemplo, con muchas nubes o con pocos años de imágenes."
        )
    parts = []
    for key, label in COMPONENT_TEXT.items():
        score = _component(result, key).get("puntaje")
        if isinstance(score, int | float):
            parts.append(f"{label} ({score:.0f} de 100)")
    confidence = CONFIDENCE_TEXT.get(result.confidence_label or "")
    explained = f"{confidence} " if confidence else ""
    return (
        f"El índice de {name} es {result.score:.0f} de 100 y se arma con: {'; '.join(parts)}. "
        f"{explained}Es lo que se ve desde el satélite: no dice por qué ni quién."
    )


def project_card(session: Session, project: Project) -> ProjectCard:
    result = latest_result(session, project.id)
    return ProjectCard(
        project_id=project.id,
        name=project.name,
        country=project.country,
        area_ha=project.area_ha,
        score=None if result is None or result.score is None else round(result.score, 1),
        category=result.category if result else None,
        confidence_label=result.confidence_label if result else None,
        forest_standing_pct=_permanence_pct(result) if result else None,
    )


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


def _ranked_line(row: dict) -> str:
    confidence = f", confianza {row['confianza']}" if row["confianza"] else ""
    return f"{_short(row['nombre'])} ({row['indice']:.0f} de 100{confidence})"


def portfolio_message(session: Session, kind: str) -> str:
    rows = [portfolio_row(project, result) for project, result in latest_results(session)]
    if not rows:
        return "Todavía no hay proyectos cargados."
    scored = [row for row in rows if row["indice"] is not None]
    if kind == "cuantos":
        counts = {
            name: sum(1 for r in scored if r["categoria"] == name) for name in PORTFOLIO_LEVELS
        }
        have = "tiene" if len(scored) == 1 else "tienen"
        return (
            f"Hay {len(rows)} proyectos cargados y {len(scored)} {have} índice calculado: "
            f"{counts['Alta']} con correspondencia alta, {counts['Media']} media y "
            f"{counts['Baja']} baja. Pregúnteme por uno por su nombre o use el botón "
            "«Elegir mi proyecto»."
        )
    ordered = sorted(scored, key=lambda row: row["indice"], reverse=kind == "mejor")[:3]
    if not ordered:
        return "Todavía no hay índices calculados para comparar."
    side = "alto" if kind == "mejor" else "bajo"
    return (
        f"Los proyectos con el índice más {side} son: "
        f"{'; '.join(_ranked_line(row) for row in ordered)}. Es lo que se ve desde el satélite, "
        "el índice es una propuesta en validación y no dice por qué ni quién."
    )
