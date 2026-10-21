from collections import defaultdict
from datetime import date, timedelta

from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process
from sqlalchemy import select

from bosquevivo.ai.agent.tools.base import Tool, ToolContext, ToolError, ToolOutput
from bosquevivo.audit.service import AuditService
from bosquevivo.db.models import ForestBaselineRecord, ForestLoss, NdviObservation, Project
from bosquevivo.registry.repository import ProjectRepository

MAX_CANDIDATES = 3
NAME_CUTOFF = 60


class BuscarProyectoArgs(BaseModel):
    texto: str | None = Field(default=None, description="Nombre aproximado del proyecto")
    lat: float | None = Field(default=None, description="Latitud")
    lon: float | None = Field(default=None, description="Longitud")


class ProyectoArgs(BaseModel):
    proyecto_id: int = Field(description="Identificador del proyecto")


class SerieArgs(BaseModel):
    proyecto_id: int
    desde_anio: int | None = None
    hasta_anio: int | None = None


class CompararArgs(BaseModel):
    proyecto_id: int
    anio_1: int
    anio_2: int


def _project(ctx: ToolContext, project_id: int) -> Project:
    project = ProjectRepository(ctx.session).get(project_id)
    if project is None:
        raise ToolError(f"el proyecto {project_id} no existe")
    return project


def _summary(project: Project) -> dict:
    return {
        "proyecto_id": project.id,
        "nombre": project.name,
        "pais": project.country,
        "area_ha": project.area_ha,
        "registro": f"{project.source_registry} {project.registry_id}",
    }


def buscar_proyecto(ctx: ToolContext, args: BuscarProyectoArgs) -> ToolOutput:
    repo = ProjectRepository(ctx.session)
    lat, lon = args.lat, args.lon
    if (lat is None or lon is None) and ctx.location:
        lat, lon = ctx.location
    if lat is not None and lon is not None:
        inside = repo.locate(lat, lon)
        if inside:
            payload = {"coincidencia": "punto dentro del polígono", **_summary(inside)}
            item = ctx.evidence.add("proyecto", f"project:{inside.id}", payload)
            return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])
        nearest = repo.nearest(lat, lon)
        if nearest and not args.texto:
            project, degrees = nearest
            payload = {
                "coincidencia": "ningún polígono contiene el punto",
                "mas_cercano": _summary(project),
                "distancia_km": round(degrees * 111.0, 1),
            }
            item = ctx.evidence.add("proyecto", f"project:{project.id}", payload)
            return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])
    if args.texto:
        projects = repo.all()
        by_id = {p.id: p for p in projects}
        names = {p.id: p.name for p in projects}
        matches = process.extract(
            args.texto,
            names,
            scorer=fuzz.WRatio,
            limit=MAX_CANDIDATES,
            score_cutoff=NAME_CUTOFF,
        )
        candidates = [
            {**_summary(by_id[pid]), "similitud": round(score)} for _, score, pid in matches
        ]
        payload = {"candidatos": candidates}
        item = ctx.evidence.add("proyecto", f"search:{args.texto}", payload)
        return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])
    raise ToolError("se necesita un nombre o una ubicación")


def obtener_auditoria(ctx: ToolContext, args: ProyectoArgs) -> ToolOutput:
    project = _project(ctx, args.proyecto_id)
    run = AuditService(ctx.session).latest(project.id)
    if run is None or run.result is None:
        payload = {"disponible": False, "proyecto": project.name}
        item = ctx.evidence.add("auditoria", f"project:{project.id}", payload)
        return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])
    result = run.result
    scores = {
        name: data.get("puntaje")
        for name, data in result.components.items()
        if not name.startswith("_") and isinstance(data, dict)
    }
    payload = {
        "disponible": True,
        "proyecto": project.name,
        "run_id": run.id,
        "indice": result.score,
        "escala_maxima": 100,
        "categoria": result.category,
        "confianza": result.confidence_label,
        "puntajes_componentes": scores,
        "fecha_calculo": run.created_at.date().isoformat(),
        "version_indice": run.index_version,
        "narrativa": result.narrative,
    }
    item = ctx.evidence.add("auditoria", f"audit_run:{run.id}", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


def _annual_ndvi(ctx: ToolContext, project_id: int) -> dict[int, tuple[float, int]]:
    rows = ctx.session.scalars(
        select(NdviObservation).where(
            NdviObservation.project_id == project_id, NdviObservation.ndvi_mean.is_not(None)
        )
    ).all()
    by_sensor: dict[str, list[NdviObservation]] = defaultdict(list)
    for row in rows:
        by_sensor[row.sensor].append(row)
    if not by_sensor:
        return {}
    chosen = max(by_sensor.values(), key=len)
    by_year: dict[int, list[float]] = defaultdict(list)
    for row in chosen:
        by_year[row.period.year].append(float(row.ndvi_mean or 0.0))
    return {y: (round(sum(v) / len(v), 3), len(v)) for y, v in sorted(by_year.items())}


def obtener_serie_ndvi(ctx: ToolContext, args: SerieArgs) -> ToolOutput:
    project = _project(ctx, args.proyecto_id)
    annual = _annual_ndvi(ctx, project.id)
    years = {
        y: v
        for y, v in annual.items()
        if (args.desde_anio is None or y >= args.desde_anio)
        and (args.hasta_anio is None or y <= args.hasta_anio)
    }
    payload = {
        "proyecto": project.name,
        "disponible": bool(years),
        "ndvi_medio_por_anio": {str(y): v[0] for y, v in years.items()},
        "meses_con_datos_por_anio": {str(y): v[1] for y, v in years.items()},
    }
    item = ctx.evidence.add("serie_ndvi", f"project:{project.id}", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


def obtener_perdida_anual(ctx: ToolContext, args: ProyectoArgs) -> ToolOutput:
    project = _project(ctx, args.proyecto_id)
    loss = ctx.session.scalars(
        select(ForestLoss).where(ForestLoss.project_id == project.id).order_by(ForestLoss.year)
    ).all()
    baseline = ctx.session.scalars(
        select(ForestBaselineRecord).where(ForestBaselineRecord.project_id == project.id)
    ).first()
    payload = {
        "proyecto": project.name,
        "disponible": bool(loss) or baseline is not None,
        "hectareas_perdidas_por_anio": {str(r.year): round(r.ha_lost, 2) for r in loss},
        "hectareas_de_bosque_inicial": round(baseline.tree_cover_ha, 2) if baseline else None,
        "fuente": "Hansen Global Forest Change",
    }
    item = ctx.evidence.add("perdida_forestal", f"project:{project.id}", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


def comparar_periodos(ctx: ToolContext, args: CompararArgs) -> ToolOutput:
    project = _project(ctx, args.proyecto_id)
    first, second = sorted((args.anio_1, args.anio_2))
    annual = _annual_ndvi(ctx, project.id)
    loss = ctx.session.scalars(
        select(ForestLoss).where(
            ForestLoss.project_id == project.id,
            ForestLoss.year > first,
            ForestLoss.year <= second,
        )
    ).all()
    ndvi_a = annual.get(first)
    ndvi_b = annual.get(second)
    payload = {
        "proyecto": project.name,
        "anio_inicial": first,
        "anio_final": second,
        "ndvi_inicial": ndvi_a[0] if ndvi_a else None,
        "ndvi_final": ndvi_b[0] if ndvi_b else None,
        "cambio_ndvi": round(ndvi_b[0] - ndvi_a[0], 3) if ndvi_a and ndvi_b else None,
        "hectareas_perdidas_en_el_periodo": round(sum(r.ha_lost for r in loss), 2),
    }
    item = ctx.evidence.add("comparacion", f"project:{project.id}:{first}-{second}", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


def window(start: date, days: int = 60) -> tuple[date, date]:
    return start, start + timedelta(days=days)


DATA_TOOLS = [
    Tool(
        "buscar_proyecto",
        "Encuentra el proyecto por nombre aproximado o por coordenadas dentro de su polígono.",
        BuscarProyectoArgs,
        buscar_proyecto,
    ),
    Tool(
        "obtener_auditoria",
        "Devuelve el último índice de correspondencia, categoría, confianza y fecha de cálculo.",
        ProyectoArgs,
        obtener_auditoria,
    ),
    Tool(
        "obtener_serie_ndvi",
        "Devuelve el NDVI medio por año de un proyecto.",
        SerieArgs,
        obtener_serie_ndvi,
    ),
    Tool(
        "obtener_perdida_anual",
        "Devuelve las hectáreas de bosque perdidas por año según Hansen y el bosque inicial.",
        ProyectoArgs,
        obtener_perdida_anual,
    ),
    Tool(
        "comparar_periodos",
        "Compara NDVI y pérdida de bosque entre dos años.",
        CompararArgs,
        comparar_periodos,
    ),
]
