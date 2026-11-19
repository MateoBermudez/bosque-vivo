from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bosquevivo.ai.agent.resolver import normalize
from bosquevivo.ai.agent.tools.base import Tool, ToolContext, ToolOutput
from bosquevivo.db.models import AuditResult, AuditRun, Project

NO_CALCULATION = "Sin calcular"
SORTERS = {
    "indice_asc": lambda row: (row["indice"] is None, row["indice"] or 0.0),
    "indice_desc": lambda row: (row["indice"] is None, -(row["indice"] or 0.0)),
    "area_desc": lambda row: (row["area_ha"] is None, -(row["area_ha"] or 0.0)),
    "nombre": lambda row: (False, row["nombre"].lower()),
}


class PortafolioArgs(BaseModel):
    orden: Literal["indice_asc", "indice_desc", "area_desc", "nombre"] = Field(
        default="indice_asc",
        description="indice_asc: peor primero; indice_desc: mejor primero; area_desc; nombre",
    )
    limite: int = Field(default=5, ge=1, le=10, description="Cuántos proyectos devolver")
    buscar: str | None = Field(
        default=None, description="Texto que debe aparecer en el nombre del proyecto"
    )


def latest_results(session: Session) -> list[tuple[Project, AuditResult | None]]:
    latest = (
        select(AuditRun.project_id, func.max(AuditRun.id).label("run_id"))
        .where(AuditRun.status == "done")
        .group_by(AuditRun.project_id)
        .subquery()
    )
    stmt = (
        select(Project, AuditResult)
        .outerjoin(latest, latest.c.project_id == Project.id)
        .outerjoin(AuditResult, AuditResult.run_id == latest.c.run_id)
        .where(Project.source_registry != "demo")
    )
    return [(row[0], row[1]) for row in session.execute(stmt).all()]


def portfolio_row(project: Project, result: AuditResult | None) -> dict:
    return {
        "proyecto_id": project.id,
        "nombre": project.name,
        "pais": project.country,
        "area_ha": project.area_ha,
        "indice": None if result is None or result.score is None else round(result.score, 1),
        "categoria": result.category if result else NO_CALCULATION,
        "confianza": result.confidence_label if result else None,
    }


def _matches(name: str, query: str | None) -> bool:
    if not query:
        return True
    haystack = normalize(name)
    return all(token in haystack for token in normalize(query).split())


def resumen_portafolio(ctx: ToolContext, args: PortafolioArgs) -> ToolOutput:
    rows = [portfolio_row(p, r) for p, r in latest_results(ctx.session)]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["categoria"]] = counts.get(row["categoria"], 0) + 1
    chosen = [row for row in rows if _matches(row["nombre"], args.buscar)]
    chosen.sort(key=SORTERS[args.orden])
    payload = {
        "total_proyectos": len(rows),
        "con_indice": sum(1 for row in rows if row["indice"] is not None),
        "por_categoria": counts,
        "coinciden": len(chosen),
        "proyectos": chosen[: args.limite],
        "nota": "No se registra departamento ni municipio de los proyectos, solo el país.",
    }
    item = ctx.evidence.add("portafolio", "portfolio", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


PORTFOLIO_TOOLS = [
    Tool(
        "resumen_portafolio",
        (
            "Resume los proyectos cargados: cuántos hay, cuántos tienen índice, cuántos por "
            "categoría, y lista los primeros según un orden (peor o mejor índice, tamaño o "
            "nombre) o los que contienen un texto en el nombre."
        ),
        PortafolioArgs,
        resumen_portafolio,
    )
]
