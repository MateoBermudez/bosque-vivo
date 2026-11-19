import json
from datetime import date

import pytest

from bosquevivo.ai.agent import Agent, AgentRequest, default_registry
from bosquevivo.ai.agent.evidence import EvidenceStore
from bosquevivo.ai.agent.tools import ToolContext
from bosquevivo.ai.llm import LLMResponse, ScriptedLLM
from bosquevivo.audit import AuditService
from bosquevivo.core.config import Settings
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.db.models import Project
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.providers import FakeProvider

RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]
NAMES = [
    ("1", "Reserva El Roble", "test"),
    ("2", "Reserva Pazcifico Norte", "test"),
    ("3", "Reserva Pazcifico Sur", "test"),
    ("4", "Concosta REDD+ Project", "test"),
    ("5", "Finca de Demostración Aurora", "demo"),
]


@pytest.fixture
def seeded(db, tmp_path):
    projects = {}
    for registry_id, name, registry in NAMES:
        project = Project(
            source_registry=registry,
            registry_id=registry_id,
            name=name,
            country="Colombia",
            start_year=2018,
            area_ha=1000.0 + int(registry_id),
            geometry=json.dumps({"type": "Polygon", "coordinates": [RING]}),
            source="test",
        )
        db.add(project)
        projects[registry_id] = project
    db.commit()
    sat = SatelliteService(db, FakeProvider(loss_by_year={2022: 14.0}), tmp_path)
    for key in ("1", "4"):
        sat.refresh_timeseries(
            projects[key].id, date(2016, 1, 1), date(2024, 12, 31), sensors=(Sensor.SENTINEL2,)
        )
        sat.refresh_forest_loss(projects[key].id)
        AuditService(db).run(projects[key].id)
    db.commit()
    return projects


def make_agent(db, script):
    llm = ScriptedLLM(script)
    return Agent(db, llm, default_registry(), Settings(admin_token="admin-secret-token")), llm


def first_envelope(llm):
    return llm.calls[0]["messages"][0].text


def test_el_sistema_identifica_el_proyecto_y_lo_consulta_antes_del_modelo(db, seeded):
    agent, llm = make_agent(db, [LLMResponse(text="Concosta tiene correspondencia alta.")])
    answer = agent.answer(AgentRequest(text="Quiero saber cómo va Concosta"))
    assert answer.tools_called == ["obtener_auditoria"]
    assert answer.project_id == seeded["4"].id
    assert not answer.used_fallback
    assert len(llm.calls) == 1
    assert "Proyecto identificado por el sistema" in first_envelope(llm)
    assert "Datos ya consultados por el sistema" in first_envelope(llm)


def test_pregunta_de_perdida_tambien_trae_la_perdida_anual(db, seeded):
    agent, _ = make_agent(db, [LLMResponse(text="Se registran pérdidas pequeñas.")])
    answer = agent.answer(AgentRequest(text="¿Hay tala en El Roble?"))
    assert answer.tools_called == ["obtener_auditoria", "obtener_perdida_anual"]


def test_si_el_nombre_es_ambiguo_pregunta_cual_sin_llamar_al_modelo(db, seeded):
    agent, llm = make_agent(db, [LLMResponse(text="no debería usarse")])
    answer = agent.answer(AgentRequest(text="cómo está Pazcifico"))
    assert llm.calls == []
    assert "Pazcifico Norte" in answer.text and "Pazcifico Sur" in answer.text
    assert not answer.used_fallback and answer.project_id is None


def down(system, messages, tools):
    raise ExternalServiceError("sin conexión")


def test_si_el_modelo_falla_responde_con_lo_ya_calculado(db, seeded):
    agent, _ = make_agent(db, down)
    answer = agent.answer(AgentRequest(text="¿Cómo está Concosta?"))
    assert answer.used_fallback
    assert "de 100" in answer.text and "Concosta" in answer.text
    assert answer.project_id == seeded["4"].id


def test_sin_proyecto_y_con_modelo_caido_explica_que_no_pudo_consultar(db, seeded):
    agent, _ = make_agent(db, down)
    answer = agent.answer(AgentRequest(text="¿Qué es el NDVI?"))
    assert answer.used_fallback
    assert "no pude consultar" in answer.text.lower()
    assert "no tengo datos suficientes" not in answer.text.lower()


def test_el_proyecto_elegido_solo_se_consulta_si_la_pregunta_es_sobre_el_proyecto(db, seeded):
    chosen = (seeded["1"].id, seeded["1"].name)
    agent, llm = make_agent(db, [LLMResponse(text="El NDVI mide qué tan verde está.")])
    answer = agent.answer(AgentRequest(text="¿Qué es el NDVI?", project=chosen))
    assert answer.tools_called == [] and answer.project_id is None
    assert "Datos ya consultados" not in first_envelope(llm)


def test_el_proyecto_elegido_se_consulta_cuando_pregunta_por_mi_bosque(db, seeded):
    chosen = (seeded["1"].id, seeded["1"].name)
    agent, llm = make_agent(db, [LLMResponse(text="Su bosque tiene correspondencia alta.")])
    answer = agent.answer(AgentRequest(text="¿Cómo está mi bosque?", project=chosen))
    assert answer.tools_called == ["obtener_auditoria"]
    assert answer.project_id == chosen[0]
    assert "Proyecto que la persona eligió" in first_envelope(llm)


def test_el_proyecto_mencionado_gana_sobre_el_elegido(db, seeded):
    chosen = (seeded["1"].id, seeded["1"].name)
    agent, _ = make_agent(db, [LLMResponse(text="Concosta tiene correspondencia alta.")])
    answer = agent.answer(AgentRequest(text="¿Y cómo va Concosta?", project=chosen))
    assert answer.project_id == seeded["4"].id


def test_proyecto_sin_auditoria_informa_el_error_al_modelo(db, seeded):
    agent, llm = make_agent(db, [LLMResponse(text="Todavía no hay un cálculo para ese proyecto.")])
    agent.answer(AgentRequest(text="cómo va Reserva Pazcifico Sur"))
    assert '"disponible": false' in first_envelope(llm)


def test_buscar_proyecto_no_confunde_frases_con_nombres(db, seeded, tmp_path):
    registry = default_registry()
    ctx = ToolContext(
        session=db,
        settings=Settings(),
        evidence=EvidenceStore(db),
        role="comunidad",
        satellite=SatelliteService(db, FakeProvider(), tmp_path),
    )
    found = registry.call("buscar_proyecto", {"texto": "bosque de Concosta"}, ctx)
    assert [c["nombre"] for c in found.content["candidatos"]] == ["Concosta REDD+ Project"]
    assert found.content["coincidencia_segura"] is True
    missing = registry.call("buscar_proyecto", {"texto": "Nube Fantasma"}, ctx)
    assert missing.content["candidatos"] == [] and "nota" in missing.content


def test_resumen_portafolio_ordena_filtra_y_excluye_la_demostracion(db, seeded, tmp_path):
    registry = default_registry()
    ctx = ToolContext(
        session=db,
        settings=Settings(),
        evidence=EvidenceStore(db),
        role="comunidad",
        satellite=SatelliteService(db, FakeProvider(), tmp_path),
    )
    summary = registry.call("resumen_portafolio", {}, ctx).content
    assert summary["total_proyectos"] == 4
    assert summary["con_indice"] == 2
    names = [row["nombre"] for row in summary["proyectos"]]
    assert "Finca de Demostración Aurora" not in names
    assert [row["indice"] is None for row in summary["proyectos"]] == sorted(
        row["indice"] is None for row in summary["proyectos"]
    )
    filtered = registry.call("resumen_portafolio", {"buscar": "pazcifico"}, ctx).content
    assert filtered["coinciden"] == 2
    best = registry.call("resumen_portafolio", {"orden": "indice_desc", "limite": 1}, ctx).content
    assert len(best["proyectos"]) == 1 and best["proyectos"][0]["indice"] is not None


def test_el_auditor_recibe_el_desglose_cuando_pide_explicar_el_indice(db, seeded):
    agent, _ = make_agent(db, [LLMResponse(text="El índice de Concosta tiene varios componentes.")])
    answer = agent.answer(AgentRequest(text="Explica el índice de Concosta", role="auditor"))
    assert answer.tools_called == ["obtener_auditoria", "explicar_indice"]


def test_la_comunidad_no_recibe_el_desglose_del_auditor(db, seeded):
    agent, _ = make_agent(db, [LLMResponse(text="Concosta tiene correspondencia alta.")])
    answer = agent.answer(AgentRequest(text="Explica el índice de Concosta"))
    assert "explicar_indice" not in answer.tools_called
    assert answer.project_id == seeded["4"].id


def test_una_pregunta_de_portafolio_no_trae_los_datos_del_proyecto_elegido(db, seeded):
    chosen = (seeded["1"].id, seeded["1"].name)
    agent, llm = make_agent(db, [LLMResponse(text="Hay cuatro proyectos.")])
    answer = agent.answer(AgentRequest(text="¿Cuál proyecto tiene el peor índice?", project=chosen))
    assert answer.tools_called == ["resumen_portafolio"] and answer.project_id is None
    assert "obtener_auditoria" not in first_envelope(llm)


def test_el_agente_devuelve_las_opciones_cuando_pregunta_cual(db, seeded):
    agent, _ = make_agent(db, [])
    answer = agent.answer(AgentRequest(text="cómo está Pazcifico"))
    assert {pid for pid, _ in answer.choices} == {seeded["2"].id, seeded["3"].id}


def test_una_comparacion_entre_dos_anios_trae_la_comparacion(db, seeded):
    agent, llm = make_agent(db, [LLMResponse(text="Hay una pérdida pequeña entre esos años.")])
    answer = agent.answer(AgentRequest(text="Compara los años 2016 y 2022 en Concosta"))
    assert answer.tools_called == ["obtener_auditoria", "comparar_periodos"]
    assert "comparar_periodos" in first_envelope(llm)


def test_un_solo_anio_no_dispara_la_comparacion(db, seeded):
    agent, _ = make_agent(db, [LLMResponse(text="En 2022 hubo una pérdida pequeña.")])
    answer = agent.answer(AgentRequest(text="¿Qué pasó en Concosta en 2022?"))
    assert "comparar_periodos" not in answer.tools_called
