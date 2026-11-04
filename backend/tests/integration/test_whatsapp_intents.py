from sqlalchemy import create_engine, inspect, text

from bosquevivo.ai.agent import Agent, default_registry
from bosquevivo.ai.llm import ScriptedLLM
from bosquevivo.assistant import AssistantService, IncomingMessage
from bosquevivo.assistant.client import RecordingClient
from bosquevivo.assistant.community import alerts_message, project_alerts, status_message
from bosquevivo.assistant.dialogue import detect_intent, is_authorized
from bosquevivo.core.config import Settings
from bosquevivo.db.models import ForestBaselineRecord, ForestLoss, WaUser
from bosquevivo.db.session import upgrade_schema
from tests.integration.test_whatsapp_flow import PHONE, SETTINGS, seeded

__all__ = ["seeded"]


def build(db, settings: Settings = SETTINGS):
    llm = ScriptedLLM([])
    client = RecordingClient(None)
    agent = Agent(db, llm, default_registry(), settings)
    return AssistantService(db, agent, client, llm, settings), client, llm


def say(service, message_id, body, phone=PHONE):
    service.handle(IncomingMessage(message_id=message_id, phone=phone, kind="text", text=body))


def onboard(service):
    say(service, "m0", "hola")
    say(service, "m1", "ACEPTO")


def test_detect_intent():
    assert detect_intent("Ayuda") == "ayuda"
    assert detect_intent("menú") == "ayuda"
    assert detect_intent("¿Hay alertas?") == "alertas"
    assert detect_intent("ESTADO") == "estado"
    assert detect_intent("¿Cómo está mi bosque?") == "estado"
    assert detect_intent("proyecto 12") == "registro"
    assert detect_intent("¿cuánto carbono capturó la reserva el roble en 2020?") is None


def test_allowlist():
    assert is_authorized("573001112233", "")
    assert is_authorized("+57 300 111 2233", "573001112233, 573009998877")
    assert not is_authorized("573000000000", "573001112233")


def test_help_without_model(db):
    service, client, llm = build(db)
    onboard(service)
    client.sent.clear()
    say(service, "m2", "ayuda")
    assert "ESTADO" in client.sent[0][1] and "ALERTAS" in client.sent[0][1]
    assert llm.calls == []


def test_alerts_require_project(db):
    service, client, _ = build(db)
    onboard(service)
    client.sent.clear()
    say(service, "m2", "alertas")
    assert "PROYECTO" in client.sent[0][1]


def test_register_then_status_and_alerts(db, seeded):
    service, client, llm = build(db)
    onboard(service)
    client.sent.clear()
    say(service, "m2", "proyecto 999")
    assert "No encontré" in client.sent[-1][1]
    say(service, "m3", f"PROYECTO {seeded.id}")
    assert "Reserva El Roble" in client.sent[-1][1]
    say(service, "m4", "estado")
    status = client.sent[-1][1]
    assert "se conserva el" in status and "% del bosque" in status
    assert "fraude" not in status.lower()
    say(service, "m5", "alertas")
    assert "Reserva El Roble" in client.sent[-1][1]
    assert llm.calls == []
    assert all(len(message) <= 300 for _, message in client.sent)


def test_location_registers_project(db, seeded):
    service, _, _ = build(db)
    onboard(service)
    service.handle(
        IncomingMessage(
            message_id="l1", phone=PHONE, kind="location", latitude=5.05, longitude=-74.95
        )
    )
    user = db.query(WaUser).one()
    assert user.project_id == seeded.id


def test_unauthorized_phone_is_not_stored(db):
    settings = SETTINGS.model_copy(update={"whatsapp_allowed_phones": "573009998877"})
    service, client, _ = build(db, settings)
    say(service, "m0", "hola")
    assert "no está habilitado" in client.sent[0][1]
    assert db.query(WaUser).count() == 0


def test_unknown_question_without_model_gets_help(db):
    service, client, _ = build(db)
    onboard(service)
    client.sent.clear()
    say(service, "m2", "cuéntame algo del clima de mañana")
    assert any("ESTADO" in message for _, message in client.sent)


def test_alert_thresholds(db, seeded):
    db.query(ForestLoss).filter(ForestLoss.project_id == seeded.id).delete()
    db.query(ForestBaselineRecord).filter(ForestBaselineRecord.project_id == seeded.id).delete()
    db.add(ForestBaselineRecord(project_id=seeded.id, tree_cover_ha=1000.0, source="t"))
    for year, lost in ((2021, 1.0), (2022, 2.0), (2023, 12.0)):
        db.add(ForestLoss(project_id=seeded.id, year=year, ha_lost=lost, source="t"))
    db.flush()
    assert project_alerts(db, seeded) == [(2023, 12.0, 1.2)]
    assert "en 2023 se perdieron 12 ha" in alerts_message(db, seeded)
    assert "se conserva" in status_message(db, seeded)


def test_upgrade_adds_missing_column(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'vieja.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE project (id INTEGER PRIMARY KEY)"))
        connection.execute(
            text("CREATE TABLE wa_user (id INTEGER PRIMARY KEY, phone_hmac VARCHAR(64))")
        )
    assert upgrade_schema(engine) == ["wa_user.project_id"]
    columns = {c["name"] for c in inspect(engine).get_columns("wa_user")}
    assert "project_id" in columns
    assert upgrade_schema(engine) == []
