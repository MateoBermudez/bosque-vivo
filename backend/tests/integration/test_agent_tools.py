import json
from datetime import date

import pytest

from bosquevivo.ai.agent import default_registry
from bosquevivo.ai.agent.evidence import EvidenceStore
from bosquevivo.ai.agent.tools import ToolContext, ToolError
from bosquevivo.ai.knowledge import KnowledgeBase
from bosquevivo.ai.llm import LLMResponse, MediaPart, ScriptedLLM
from bosquevivo.audit import AuditService
from bosquevivo.core.config import Settings
from bosquevivo.db.models import Evidence, Project
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.providers import FakeProvider

RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]
QUALITY_OK = json.dumps(
    {"nubes": "bajo", "humo": "no", "sombras": "no", "utilizable": "si", "motivo": "clara"}
)
QUALITY_BAD = json.dumps(
    {"nubes": "alto", "humo": "no", "sombras": "no", "utilizable": "no", "motivo": "nubes"}
)


@pytest.fixture
def seeded(db, tmp_path):
    items = []
    for registry_id, name, offset in (
        ("1", "Reserva El Roble", 0.0),
        ("2", "Finca La Aurora", 1.0),
    ):
        ring = [[x + offset, y] for x, y in RING]
        items.append(
            Project(
                source_registry="test",
                registry_id=registry_id,
                name=name,
                country="Colombia",
                start_year=2018,
                area_ha=900.0,
                geometry=json.dumps({"type": "Polygon", "coordinates": [ring]}),
                source="test",
            )
        )
    db.add_all(items)
    db.commit()
    sat = SatelliteService(db, FakeProvider(loss_by_year={2022: 14.0}), tmp_path)
    sat.refresh_timeseries(
        items[0].id, date(2016, 1, 1), date(2024, 12, 31), sensors=(Sensor.SENTINEL2,)
    )
    sat.refresh_forest_loss(items[0].id)
    AuditService(db).run(items[0].id)
    db.commit()
    return items


def context(db, tmp_path, llm=None, role="auditor", **extra):
    return ToolContext(
        session=db,
        settings=Settings(),
        evidence=EvidenceStore(db),
        role=role,
        llm=llm,
        satellite=SatelliteService(db, FakeProvider(), tmp_path),
        **extra,
    )


def run(name, ctx, **args):
    return default_registry().call(name, args, ctx)


def test_search_by_approximate_name(db, seeded, tmp_path):
    out = run("buscar_proyecto", context(db, tmp_path), texto="roble reserva")
    assert out.content["candidatos"][0]["nombre"] == "Reserva El Roble"


def test_search_by_coordinates_inside_polygon(db, seeded, tmp_path):
    out = run("buscar_proyecto", context(db, tmp_path), lat=5.05, lon=-74.95)
    assert out.content["nombre"] == "Reserva El Roble"


def test_search_uses_context_location(db, seeded, tmp_path):
    ctx = context(db, tmp_path, location=(5.05, 1.0 - 74.95))
    out = run("buscar_proyecto", ctx)
    assert out.content["nombre"] == "Finca La Aurora"


def test_search_requires_name_or_location(db, seeded, tmp_path):
    with pytest.raises(ToolError):
        run("buscar_proyecto", context(db, tmp_path))


def test_audit_tool_returns_scale_and_evidence(db, seeded, tmp_path):
    ctx = context(db, tmp_path)
    out = run("obtener_auditoria", ctx, proyecto_id=seeded[0].id)
    assert out.content["disponible"] and out.content["escala_maxima"] == 100
    assert db.get(Evidence, out.evidence_ids[0]) is not None


def test_audit_tool_without_run_reports_unavailable(db, seeded, tmp_path):
    out = run("obtener_auditoria", context(db, tmp_path), proyecto_id=seeded[1].id)
    assert out.content["disponible"] is False


def test_invalid_arguments_raise_tool_error(db, seeded, tmp_path):
    with pytest.raises(ToolError):
        run("obtener_auditoria", context(db, tmp_path), proyecto_id="abc")
    with pytest.raises(ToolError):
        run("obtener_auditoria", context(db, tmp_path), proyecto_id=9999)


def test_loss_and_comparison_tools(db, seeded, tmp_path):
    ctx = context(db, tmp_path)
    loss = run("obtener_perdida_anual", ctx, proyecto_id=seeded[0].id)
    assert loss.content["hectareas_perdidas_por_anio"] == {"2022": 14.0}
    diff = run("comparar_periodos", ctx, proyecto_id=seeded[0].id, anio_1=2024, anio_2=2020)
    assert diff.content["anio_inicial"] == 2020
    assert diff.content["hectareas_perdidas_en_el_periodo"] == 14.0


def test_knowledge_tool_cites_source(db, seeded, tmp_path):
    KnowledgeBase(db).load_directory()
    out = run("buscar_conocimiento", context(db, tmp_path), consulta="¿Qué es el NDVI?")
    assert out.content["encontrado"]
    assert " · " in out.content["resultados"][0]["cita"]


def test_explain_index_includes_weights(db, seeded, tmp_path):
    out = run("explicar_indice", context(db, tmp_path), proyecto_id=seeded[0].id)
    assert out.content["pesos"]["permanencia"] == 0.5


def test_request_calculation_enqueues_job(db, seeded, tmp_path):
    out = run("solicitar_calculo", context(db, tmp_path), proyecto_id=seeded[1].id)
    assert out.content["estado"] == "en cola"


def test_images_tool_returns_media_when_usable(db, seeded, tmp_path):
    llm = ScriptedLLM(
        [
            LLMResponse(text=QUALITY_OK),
            LLMResponse(text=QUALITY_OK),
            LLMResponse(text="Se ve un claro al noreste."),
        ]
    )
    out = run(
        "ver_imagenes",
        context(db, tmp_path, llm=llm),
        proyecto_id=seeded[0].id,
        fecha_antes="2020-01-01",
        fecha_despues="2023-01-01",
    )
    assert out.content["ambas_utilizables"] and len(out.media) == 2
    assert out.content["descripcion_visual"] == "Se ve un claro al noreste."


def test_images_tool_refuses_to_conclude_with_bad_quality(db, seeded, tmp_path):
    llm = ScriptedLLM([LLMResponse(text=QUALITY_OK), LLMResponse(text=QUALITY_BAD)])
    out = run(
        "ver_imagenes",
        context(db, tmp_path, llm=llm),
        proyecto_id=seeded[0].id,
        fecha_antes="2020-01-01",
        fecha_despues="2023-01-01",
    )
    assert not out.content["ambas_utilizables"]
    assert out.content["descripcion_visual"] is None
    assert out.media == []


def test_images_tool_validates_date_order(db, seeded, tmp_path):
    with pytest.raises(ToolError):
        run(
            "ver_imagenes",
            context(db, tmp_path, llm=ScriptedLLM([])),
            proyecto_id=seeded[0].id,
            fecha_antes="2023-01-01",
            fecha_despues="2020-01-01",
        )


def test_user_photo_requires_consent(db, seeded, tmp_path):
    photo = [MediaPart(b"img", "image/jpeg")]
    ctx = context(db, tmp_path, llm=ScriptedLLM([LLMResponse(text="Un claro")]), user_media=photo)
    with pytest.raises(ToolError):
        run("analizar_foto_usuario", ctx)


def test_user_photo_is_marked_unverified(db, seeded, tmp_path):
    photo = [MediaPart(b"img", "image/jpeg")]
    ctx = context(
        db,
        tmp_path,
        llm=ScriptedLLM([LLMResponse(text="Se ven troncos cortados.")]),
        user_media=photo,
        media_consent=True,
    )
    out = run("analizar_foto_usuario", ctx)
    assert out.content["verificada"] is False
