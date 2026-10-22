from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy import select

from bosquevivo.ai.agent.tools.base import Tool, ToolContext, ToolError, ToolOutput
from bosquevivo.ai.agent.tools.data import ProyectoArgs, window
from bosquevivo.ai.knowledge import KnowledgeBase
from bosquevivo.ai.llm import MediaPart
from bosquevivo.ai.vision import assess_scene_quality, describe_change, describe_user_photo
from bosquevivo.audit.service import AuditService
from bosquevivo.db.models import AuditRun, ImageAsset
from bosquevivo.jobs.kinds import CALCULATE_AUDIT, GENERATE_REPORT
from bosquevivo.jobs.queue import JobQueue
from bosquevivo.satellite.models import Sensor, ThumbnailKind


class ImagenesArgs(BaseModel):
    proyecto_id: int
    fecha_antes: date = Field(description="Fecha aproximada de la imagen anterior (YYYY-MM-DD)")
    fecha_despues: date = Field(description="Fecha aproximada de la imagen posterior")


class ConocimientoArgs(BaseModel):
    consulta: str = Field(description="Pregunta sobre metodología, glosario, normativa o FAQ")


class ReporteArgs(BaseModel):
    run_id: int
    formato: str = Field(default="html", description="html o pdf")


def ver_imagenes(ctx: ToolContext, args: ImagenesArgs) -> ToolOutput:
    if ctx.satellite is None or ctx.llm is None:
        raise ToolError("el análisis de imágenes no está disponible en este momento")
    if args.fecha_antes >= args.fecha_despues:
        raise ToolError("la fecha anterior debe ser menor que la posterior")
    sides: list[tuple[str, ImageAsset]] = []
    for label, start in (("antes", args.fecha_antes), ("despues", args.fecha_despues)):
        begin, end = window(start)
        asset = ctx.satellite.thumbnail(
            args.proyecto_id, begin, end, ThumbnailKind.NATURAL, Sensor.SENTINEL2
        )
        sides.append((label, asset))
    media: list[MediaPart] = []
    qualities: dict[str, dict] = {}
    for label, asset in sides:
        part = MediaPart(Path(asset.path).read_bytes(), "image/png")
        media.append(part)
        quality = assess_scene_quality(ctx.llm, part)
        asset.quality = quality.model_dump()
        qualities[label] = quality.model_dump()
    usable = all(q["utilizable"] == "si" for q in qualities.values())
    payload: dict = {
        "calidad": qualities,
        "ambas_utilizables": usable,
        "imagen_antes_id": sides[0][1].id,
        "imagen_despues_id": sides[1][1].id,
    }
    if usable:
        payload["descripcion_visual"] = describe_change(ctx.llm, media[0], media[1])
    else:
        payload["descripcion_visual"] = None
        payload["aviso"] = "las imágenes no son aptas para comparar; no se puede concluir"
    item = ctx.evidence.add("imagenes", f"project:{args.proyecto_id}", payload)
    return ToolOutput(
        payload | {"evidencia_id": item.id},
        media=media if usable else [],
        evidence_ids=[item.id],
    )


def buscar_conocimiento(ctx: ToolContext, args: ConocimientoArgs) -> ToolOutput:
    hits = KnowledgeBase(ctx.session).search(args.consulta)
    payload = {
        "resultados": [{"cita": h.citation, "texto": h.content} for h in hits],
        "encontrado": bool(hits),
    }
    item = ctx.evidence.add("conocimiento", f"kb:{args.consulta[:60]}", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


def explicar_indice(ctx: ToolContext, args: ProyectoArgs) -> ToolOutput:
    run = AuditService(ctx.session).latest(args.proyecto_id)
    if run is None or run.result is None:
        raise ToolError("el proyecto no tiene una auditoría calculada")
    components = {
        name: data
        for name, data in run.result.components.items()
        if not name.startswith("_") and isinstance(data, dict)
    }
    payload = {
        "run_id": run.id,
        "indice": run.result.score,
        "escala_maxima": 100,
        "componentes": components,
        "sensibilidad": run.result.components.get("_sensibilidad"),
        "sensor": run.result.components.get("_sensor"),
        "pesos": {
            "permanencia": run.parameters.get("weight_permanence"),
            "evolucion_perdida": run.parameters.get("weight_evolution"),
            "tendencia": run.parameters.get("weight_trend"),
            "estabilidad": run.parameters.get("weight_stability"),
        },
        "version_indice": run.index_version,
    }
    item = ctx.evidence.add("explicacion_indice", f"audit_run:{run.id}", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


def solicitar_calculo(ctx: ToolContext, args: ProyectoArgs) -> ToolOutput:
    pending = ctx.session.scalars(
        select(AuditRun).where(
            AuditRun.project_id == args.proyecto_id, AuditRun.status == "running"
        )
    ).first()
    if pending:
        raise ToolError("ya hay un cálculo en curso para ese proyecto")
    job = JobQueue(ctx.session).enqueue(CALCULATE_AUDIT, {"project_id": args.proyecto_id})
    payload = {"trabajo_id": job.id, "estado": "en cola"}
    item = ctx.evidence.add("trabajo", f"job:{job.id}", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


def generar_reporte(ctx: ToolContext, args: ReporteArgs) -> ToolOutput:
    if args.formato not in {"html", "pdf"}:
        raise ToolError("el formato debe ser html o pdf")
    job = JobQueue(ctx.session).enqueue(
        GENERATE_REPORT, {"run_id": args.run_id, "format": args.formato}
    )
    payload = {"trabajo_id": job.id, "estado": "en cola", "formato": args.formato}
    item = ctx.evidence.add("trabajo", f"job:{job.id}", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


class SinArgumentos(BaseModel):
    pass


def analizar_foto_usuario(ctx: ToolContext, args: SinArgumentos) -> ToolOutput:
    if not ctx.media_consent:
        raise ToolError("la persona no ha autorizado el uso de fotos")
    if ctx.llm is None or not ctx.user_media:
        raise ToolError("no hay una foto para analizar")
    image = ctx.user_media[0]
    description = describe_user_photo(ctx.llm, image)
    payload = {
        "descripcion": description,
        "verificada": False,
        "ubicacion_enviada": ctx.location is not None,
        "aviso": "evidencia comunitaria no verificada",
    }
    item = ctx.evidence.add("foto_usuario", "user_photo", payload)
    return ToolOutput(payload | {"evidencia_id": item.id}, evidence_ids=[item.id])


EXTRA_TOOLS = [
    Tool(
        "ver_imagenes",
        ("Genera imágenes satelitales antes y después, evalúa su calidad y describe diferencias."),
        ImagenesArgs,
        ver_imagenes,
    ),
    Tool(
        "buscar_conocimiento",
        ("Busca en la base de conocimiento (metodología, glosario, normativa, FAQ) con cita."),
        ConocimientoArgs,
        buscar_conocimiento,
    ),
    Tool(
        "analizar_foto_usuario",
        ("Describe la foto enviada por la persona, con su autorización. Evidencia no verificada."),
        SinArgumentos,
        analizar_foto_usuario,
    ),
    Tool(
        "explicar_indice",
        "Desglosa los componentes, pesos y sensibilidad del último índice de un proyecto.",
        ProyectoArgs,
        explicar_indice,
        roles=("auditor",),
    ),
    Tool(
        "solicitar_calculo",
        "Encola el cálculo completo de la auditoría de un proyecto.",
        ProyectoArgs,
        solicitar_calculo,
        roles=("auditor",),
    ),
    Tool(
        "generar_reporte",
        "Encola la generación del reporte de una corrida de auditoría en html o pdf.",
        ReporteArgs,
        generar_reporte,
        roles=("auditor",),
    ),
]
