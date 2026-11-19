import json
from datetime import date

import pytest

from bosquevivo.ai.agent import Agent, default_registry
from bosquevivo.ai.llm import LLMResponse, ScriptedLLM
from bosquevivo.api.deps import get_assistant_llm, get_satellite_provider
from bosquevivo.assistant import AssistantService, IncomingMessage
from bosquevivo.assistant.client import RecordingClient
from bosquevivo.assistant.community import index_message, project_card, status_message
from bosquevivo.assistant.dialogue import (
    detect_intent,
    detect_portfolio,
    detect_topic,
)
from bosquevivo.audit import AuditService
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.db.models import Project, WaUser
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.providers import FakeProvider
from tests.integration.test_whatsapp_flow import PHONE, SETTINGS

RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]
ADMIN = {"X-Admin-Token": "secreto"}
REF = "guia-0001-abcd"


@pytest.fixture
def seeded(db, tmp_path):
    projects = {}
    for registry_id, name in (
        ("1", "Reserva El Roble"),
        ("2", "Reserva Pazcifico Norte"),
        ("3", "Reserva Pazcifico Sur"),
    ):
        project = Project(
            source_registry="test",
            registry_id=registry_id,
            name=name,
            country="Colombia",
            start_year=2018,
            area_ha=1000.0,
            geometry=json.dumps({"type": "Polygon", "coordinates": [RING]}),
            source="test",
        )
        db.add(project)
        projects[registry_id] = project
    db.commit()
    sat = SatelliteService(db, FakeProvider(loss_by_year={2022: 14.0}), tmp_path)
    roble = projects["1"]
    sat.refresh_timeseries(
        roble.id, date(2016, 1, 1), date(2024, 12, 31), sensors=(Sensor.SENTINEL2,)
    )
    sat.refresh_forest_loss(roble.id)
    AuditService(db).run(roble.id)
    db.commit()
    return projects


def build(db, script):
    llm = ScriptedLLM(script)
    client = RecordingClient(None)
    agent = Agent(db, llm, default_registry(), SETTINGS)
    return AssistantService(db, agent, client, llm, SETTINGS), client, llm


def say(service, message_id, body):
    service.handle(IncomingMessage(message_id=message_id, phone=PHONE, kind="text", text=body))


def onboard(service):
    say(service, "m0", "hola")
    say(service, "m1", "ACEPTO")


def test_detecta_saludo_gracias_y_quien_eres():
    assert detect_intent("Hola") == "saludo"
    assert detect_intent("buenas tardes") == "saludo"
    assert detect_intent("muchas gracias") == "gracias"
    assert detect_intent("¿Quién eres?") == "quien"
    assert detect_intent("¿Qué puedes hacer?") == "quien"
    assert detect_intent("hola, ¿cómo está el roble?") is None
    assert detect_intent("¿Hay alertas?") is None
    assert detect_intent("alertas") == "alertas"


def test_detecta_el_tema_de_una_pregunta_corta():
    assert detect_topic("¿Hay tala en mi finca?") == "alertas"
    assert detect_topic("explícame el índice") == "indice"
    assert detect_topic("¿cómo va el proyecto?") == "estado"
    assert detect_topic("¿cómo se calcula la permanencia forestal en detalle para todos?") is None


def envelope(llm, position=0):
    return llm.calls[position]["messages"][0].text


def test_saludo_gracias_y_quien_eres_los_responde_el_modelo(db, seeded):
    script = [
        LLMResponse(text="Hola, cuénteme de qué proyecto quiere saber."),
        LLMResponse(text="Con mucho gusto."),
        LLMResponse(text="Soy el asistente de Bosque Vivo, una inteligencia artificial."),
    ]
    service, client, llm = build(db, script)
    onboard(service)
    client.sent.clear()
    say(service, "m2", "hola")
    say(service, "m3", "gracias")
    say(service, "m4", "¿quién eres?")
    assert [text for _, text in client.sent] == [r.text for r in script]
    assert len(llm.calls) == 3 and all(call["light"] for call in llm.calls)


def test_si_el_modelo_falla_el_saludo_y_los_agradecimientos_usan_plantilla(db, seeded):
    service, client, _ = build(db, [])
    onboard(service)
    client.sent.clear()
    say(service, "m2", "hola")
    say(service, "m3", "gracias")
    say(service, "m4", "¿quién eres?")
    assert "elíjalo" in client.sent[0][1]
    assert "Con gusto" in client.sent[1][1]
    assert "inteligencia artificial" in client.sent[2][1]


def test_preguntar_por_el_nombre_lo_responde_el_modelo_con_los_datos_ya_consultados(db, seeded):
    service, client, llm = build(db, [LLMResponse(text="Reserva El Roble se ve bien.")])
    onboard(service)
    client.sent.clear()
    say(service, "m2", "¿Cómo está el bosque de Reserva El Roble?")
    assert client.sent[0][1] == "Reserva El Roble se ve bien."
    assert len(llm.calls) == 1 and llm.calls[0]["light"]
    assert "Datos ya consultados" in envelope(llm) and "obtener_auditoria" in envelope(llm)
    assert db.query(WaUser).one().project_id == seeded["1"].id
    assert service.turn_project_id == seeded["1"].id


def test_el_nombre_dentro_de_una_frase_con_tema_de_alertas(db, seeded):
    service, client, llm = build(db, [LLMResponse(text="No veo alertas por ahora.")])
    onboard(service)
    client.sent.clear()
    say(service, "m2", "¿hay tala en el Roble?")
    assert "No veo alertas" in client.sent[0][1]
    assert "obtener_perdida_anual" in envelope(llm)


def test_si_hay_dos_proyectos_parecidos_pregunta_cual(db, seeded):
    service, client, llm = build(db, [])
    onboard(service)
    client.sent.clear()
    say(service, "m2", "¿cómo está Pazcifico?")
    assert "Pazcifico Norte" in client.sent[0][1] and "Pazcifico Sur" in client.sent[0][1]
    assert llm.calls == []
    assert db.query(WaUser).one().project_id is None


def test_mencionar_otro_proyecto_cambia_el_proyecto_de_la_conversacion(db, seeded):
    script = [
        LLMResponse(text="Primero El Roble."),
        LLMResponse(text="Ahora Pazcifico Sur."),
        LLMResponse(text="Sin alertas."),
    ]
    service, client, llm = build(db, script)
    onboard(service)
    say(service, "m2", "¿Cómo está Reserva El Roble?")
    assert db.query(WaUser).one().project_id == seeded["1"].id
    client.sent.clear()
    say(service, "m3", "¿Y cómo está Reserva Pazcifico Sur?")
    assert db.query(WaUser).one().project_id == seeded["3"].id
    assert client.sent[0][1] == "Ahora Pazcifico Sur."
    say(service, "m4", "¿hay alertas?")
    assert "Reserva Pazcifico Sur" in envelope(llm, 2)


def test_una_pregunta_de_metodologia_no_se_confunde_con_el_estado(db, seeded):
    service, client, llm = build(db, [LLMResponse(text="Se calcula con tres o cuatro partes.")])
    onboard(service)
    say(service, "m2", f"proyecto {seeded['1'].id}")
    client.sent.clear()
    say(service, "m3", "¿cómo se calcula el índice?")
    assert "tres o cuatro partes" in client.sent[0][1]
    assert len(llm.calls) == 1


def test_una_pregunta_ajena_con_proyecto_elegido_va_al_modelo(db, seeded):
    service, client, llm = build(db, [LLMResponse(text="Solo puedo ayudarle con Bosque Vivo.")])
    onboard(service)
    say(service, "m2", f"proyecto {seeded['1'].id}")
    client.sent.clear()
    say(service, "m3", "¿cómo está el clima?")
    assert "Bosque Vivo" in client.sent[0][1]
    assert len(llm.calls) == 1


def test_el_indice_de_mi_proyecto_lo_explica_el_modelo_con_los_datos_del_proyecto(db, seeded):
    service, client, llm = build(db, [LLMResponse(text="Es la nota que resume el bosque.")])
    onboard(service)
    say(service, "m2", f"proyecto {seeded['1'].id}")
    client.sent.clear()
    say(service, "m3", "¿qué significa el índice de mi proyecto?")
    assert "nota que resume" in client.sent[0][1]
    assert len(llm.calls) == 1 and "obtener_auditoria" in envelope(llm)


def test_si_la_ia_falla_responde_con_lo_ya_calculado(db, seeded):
    def down(system, messages, tools):
        raise ExternalServiceError("saturado")

    service, client, _ = build(db, down)
    onboard(service)
    client.sent.clear()
    say(service, "m2", "¿Cuánto carbono capturó la reserva el roble en 2020?")
    reply = client.sent[0][1]
    assert "esto es lo que ya está calculado" in reply
    assert "Reserva El Roble" in reply and "se conserva el" in reply


def test_estado_sin_proyecto_pide_elegirlo(db, seeded):
    service, client, _ = build(db, [])
    onboard(service)
    client.sent.clear()
    say(service, "m2", "estado")
    assert "Elegir mi proyecto" in client.sent[0][1]


def test_los_comandos_estado_y_alertas_no_usan_el_modelo(db, seeded):
    service, client, llm = build(db, [])
    onboard(service)
    say(service, "m2", f"proyecto {seeded['1'].id}")
    client.sent.clear()
    say(service, "m3", "ESTADO")
    say(service, "m4", "ALERTAS")
    assert "se conserva el" in client.sent[0][1]
    assert "alertas" in client.sent[1][1].lower()
    assert llm.calls == []


def test_los_mensajes_largos_se_parten_con_el_limite_de_la_web(db, seeded):
    service, client, _ = build(db, [])
    onboard(service)
    client.sent.clear()
    say(service, "m2", "¿Cómo está Reserva El Roble?")
    assert len(client.sent) == 1


def test_la_ficha_del_proyecto_trae_los_datos_del_ultimo_calculo(db, seeded):
    card = project_card(db, seeded["1"])
    assert card.project_id == seeded["1"].id and card.score is not None
    assert card.category and card.forest_standing_pct is not None
    empty = project_card(db, seeded["2"])
    assert empty.score is None and empty.category is None


def test_estado_e_indice_de_un_proyecto_sin_calculo(db, seeded):
    assert "Todavía no hemos revisado" in status_message(db, seeded["2"])
    assert "Todavía no hemos calculado" in index_message(db, seeded["2"])


def send(client, message):
    return client.post(
        "/api/v1/community/messages", headers=ADMIN, json={"session_ref": REF, "message": message}
    ).json()


def test_la_api_devuelve_sugerencias_segun_la_etapa_y_la_ficha(client, db, seeded):
    client.app.dependency_overrides[get_assistant_llm] = lambda: ScriptedLLM([])
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    first = send(client, "hola")
    assert [s["message"] for s in first["suggestions"]] == ["ACEPTO"] and first["project"] is None
    consent = send(client, "ACEPTO")
    actions = {s["action"] for s in consent["suggestions"]}
    assert {"elegir_proyecto", "ubicacion"} <= actions
    answer = send(client, "¿Cómo está Reserva El Roble?")
    assert answer["project"]["name"] == "Reserva El Roble"
    assert answer["project"]["score"] is not None
    labels = [s["label"] for s in answer["suggestions"]]
    assert "¿Hay alertas?" in labels and "Cambiar de proyecto" in labels
    deleted = send(client, "BORRAR MIS DATOS")
    assert [s["message"] for s in deleted["suggestions"]] == ["Hola"]


def test_detecta_preguntas_sobre_todos_los_proyectos():
    assert detect_portfolio("¿Cuál proyecto tiene el peor índice?") == "peor"
    assert detect_portfolio("¿cuál tiene el mejor índice?") == "mejor"
    assert detect_portfolio("¿Cuántos proyectos hay?") == "cuantos"
    assert detect_portfolio("¿Qué proyectos hay cargados?") == "cuantos"
    assert detect_portfolio("¿Qué proyectos hay en el Chocó?") is None
    assert detect_portfolio("¿qué tan mal está mi índice?") is None


def test_las_preguntas_de_portafolio_las_responde_el_modelo_con_el_resumen(db, seeded):
    script = [LLMResponse(text="Hay tres proyectos cargados."), LLMResponse(text="El peor es uno.")]
    service, client, llm = build(db, script)
    onboard(service)
    say(service, "m2", f"proyecto {seeded['1'].id}")
    client.sent.clear()
    say(service, "m3", "¿Cuántos proyectos hay?")
    assert "tres proyectos" in client.sent[0][1]
    assert "resumen_portafolio" in envelope(llm)
    say(service, "m4", "¿Cuál proyecto tiene el peor índice?")
    assert "resumen_portafolio" in envelope(llm, 1)
    assert Agent._portfolio_plan("¿cuál tiene el peor índice?")[0][1]["orden"] == "indice_asc"
    assert Agent._portfolio_plan("¿cuál tiene el mejor índice?")[0][1]["orden"] == "indice_desc"
    assert Agent._portfolio_plan("¿cómo está el clima?") == []


def test_si_el_modelo_falla_el_portafolio_se_responde_con_lo_calculado(db, seeded):
    service, client, _ = build(db, [])
    onboard(service)
    client.sent.clear()
    say(service, "m2", "¿Cuántos proyectos hay?")
    assert "Hay 3 proyectos cargados y 1 tiene índice calculado" in client.sent[0][1]
    say(service, "m3", "¿Cuál proyecto tiene el peor índice?")
    assert "índice más bajo" in client.sent[1][1] and "Reserva El Roble" in client.sent[1][1]
    assert service.turn_project_id is None


def test_elegir_un_proyecto_muestra_su_estado_de_una_vez(db, seeded):
    service, client, _ = build(db, [])
    onboard(service)
    client.sent.clear()
    say(service, "m2", f"proyecto {seeded['1'].id}")
    reply = client.sent[0][1]
    assert "quedó registrado el proyecto Reserva El Roble" in reply and "se conserva el" in reply
    assert service.turn_project_id == seeded["1"].id


def test_la_confianza_se_explica_en_palabras(db, seeded):
    assert "La confianza es" in index_message(db, seeded["1"])
    service, client, _ = build(db, [])
    onboard(service)
    say(service, "m2", f"proyecto {seeded['1'].id}")
    client.sent.clear()
    say(service, "m3", "¿Qué tan seguro es ese resultado?")
    assert "La confianza es" in client.sent[0][1]


def test_con_dos_proyectos_parecidos_se_ofrecen_como_botones(client, db, seeded):
    client.app.dependency_overrides[get_assistant_llm] = lambda: ScriptedLLM([])
    client.app.dependency_overrides[get_satellite_provider] = lambda: None
    send(client, "hola")
    send(client, "ACEPTO")
    answer = send(client, "¿cómo está Pazcifico?")
    options = {s["label"]: s["message"] for s in answer["suggestions"] if s["message"]}
    assert options == {
        "Reserva Pazcifico Norte": f"PROYECTO {seeded['2'].id}",
        "Reserva Pazcifico Sur": f"PROYECTO {seeded['3'].id}",
    }
    assert any(s["action"] == "elegir_proyecto" for s in answer["suggestions"])
    chosen = send(client, f"PROYECTO {seeded['3'].id}")
    assert chosen["project"]["name"] == "Reserva Pazcifico Sur"


def test_una_pregunta_corta_de_tala_con_proyecto_elegido_consulta_las_perdidas(db, seeded):
    service, client, llm = build(db, [LLMResponse(text="No veo tala reciente.")])
    onboard(service)
    say(service, "m2", f"proyecto {seeded['1'].id}")
    client.sent.clear()
    say(service, "m3", "¿Hay tala?")
    assert "No veo tala" in client.sent[0][1]
    assert "obtener_perdida_anual" in envelope(llm)
