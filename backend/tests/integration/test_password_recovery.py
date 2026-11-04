import re
from datetime import timedelta

import pytest

from bosquevivo.accounts import (
    GENERIC_RESET_MESSAGE,
    AccountService,
    MemoryMailer,
    OutboxMailer,
    OutgoingEmail,
    SmtpMailer,
    TokenStatus,
    build_mailer,
)
from bosquevivo.accounts.passwords import hash_password, password_problems, verify_password
from bosquevivo.api.routers.auth import get_mailer
from bosquevivo.core.config import Settings
from bosquevivo.core.errors import ExternalServiceError, ValidationFailedError
from bosquevivo.db.base import utcnow
from bosquevivo.db.models import Incident, PasswordResetToken

ADMIN = {"X-Admin-Token": "secreto"}
EMAIL = "auditora@elpoli.edu.co"
PASSWORD = "BosqueVivo2026"


class Clock:
    def __init__(self) -> None:
        self.now = utcnow()

    def __call__(self):
        return self.now

    def advance(self, minutes: int) -> None:
        self.now += timedelta(minutes=minutes)


def token_from(mail: OutgoingEmail) -> str:
    match = re.search(r"token=([\w-]+)", mail.body)
    assert match
    return match.group(1)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def mailer():
    return MemoryMailer()


@pytest.fixture
def service(db, mailer, clock):
    accounts = AccountService(
        db,
        mailer,
        Settings(web_base_url="https://bosque.test", password_reset_ttl_minutes=30),
        clock,
    )
    accounts.create_user(EMAIL, "Auditora", PASSWORD)
    return accounts


def test_password_hash_roundtrip_and_salt():
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert first != second
    assert verify_password(PASSWORD, first)
    assert not verify_password("otra-clave-123", first)
    assert not verify_password(PASSWORD, "texto-cualquiera")


def test_password_policy():
    assert password_problems("corta1")
    assert password_problems("solamenteletras")
    assert password_problems("1234567890123")
    assert password_problems("a@b.co12345A", "a@b.co12345a")
    assert password_problems(PASSWORD) == []


def test_create_user_rejects_duplicates_and_bad_input(service):
    with pytest.raises(ValidationFailedError):
        service.create_user(EMAIL.upper(), "Otra", PASSWORD)
    with pytest.raises(ValidationFailedError):
        service.create_user("sin-arroba", "X", PASSWORD)
    with pytest.raises(ValidationFailedError):
        service.create_user("nuevo@elpoli.edu.co", "X", "debil")


def test_authenticate_and_lock_after_failures(service, clock):
    assert service.authenticate(EMAIL, PASSWORD).user is not None
    assert service.authenticate("nadie@elpoli.edu.co", PASSWORD).user is None
    for _ in range(5):
        assert service.authenticate(EMAIL, "incorrecta-123").user is None
    assert service.authenticate(EMAIL, PASSWORD).locked
    clock.advance(11)
    assert service.authenticate(EMAIL, PASSWORD).user is not None


def test_reset_flow_sends_single_use_link(service, mailer, clock):
    assert service.request_reset(EMAIL) == GENERIC_RESET_MESSAGE
    assert len(mailer.sent) == 1
    mail = mailer.sent[0]
    assert mail.to == EMAIL
    assert "https://bosque.test/acceso/restablecer?token=" in mail.body
    assert "30 minutos" in mail.body
    token = token_from(mail)
    assert service.token_status(token) is TokenStatus.VALID
    service.confirm_reset(token, "NuevaClave2026")
    assert service.authenticate(EMAIL, "NuevaClave2026").user is not None
    assert service.authenticate(EMAIL, PASSWORD).user is None
    assert service.token_status(token) is TokenStatus.USED


def test_unknown_email_gets_same_message_and_no_mail(service, mailer):
    assert service.request_reset("desconocido@elpoli.edu.co") == GENERIC_RESET_MESSAGE
    assert mailer.sent == []


def test_token_expires(service, mailer, clock):
    service.request_reset(EMAIL)
    token = token_from(mailer.sent[0])
    clock.advance(31)
    assert service.token_status(token) is TokenStatus.EXPIRED
    with pytest.raises(ValidationFailedError, match="venció"):
        service.confirm_reset(token, "NuevaClave2026")


def test_new_request_invalidates_previous_token(service, mailer):
    service.request_reset(EMAIL)
    service.request_reset(EMAIL)
    first, second = (token_from(m) for m in mailer.sent)
    assert service.token_status(first) is TokenStatus.USED
    assert service.token_status(second) is TokenStatus.VALID


def test_token_is_stored_hashed(service, mailer, db):
    service.request_reset(EMAIL)
    token = token_from(mailer.sent[0])
    stored = db.query(PasswordResetToken).one()
    assert stored.token_hash != token and len(stored.token_hash) == 64


def test_reset_requests_are_throttled(service, mailer):
    for _ in range(5):
        service.request_reset(EMAIL)
    assert len(mailer.sent) == 3


def test_invalid_token_and_weak_password(service, mailer):
    assert service.token_status("no-existe") is TokenStatus.INVALID
    service.request_reset(EMAIL)
    token = token_from(mailer.sent[0])
    with pytest.raises(ValidationFailedError, match="al menos"):
        service.confirm_reset(token, "corta")
    assert service.token_status(token) is TokenStatus.VALID


def test_disabled_user_cannot_login_or_reset(service, mailer):
    service.set_active(EMAIL, False)
    assert service.authenticate(EMAIL, PASSWORD).user is None
    service.request_reset(EMAIL)
    assert mailer.sent == []


def test_mail_failure_is_recorded_as_external_incident(db, clock):
    class BrokenMailer:
        name = "roto"

        def send(self, message):
            raise ExternalServiceError("smtp caído")

    accounts = AccountService(db, BrokenMailer(), Settings(), clock)
    accounts.create_user(EMAIL, "Auditora", PASSWORD)
    assert accounts.request_reset(EMAIL) == GENERIC_RESET_MESSAGE
    incident = db.query(Incident).one()
    assert incident.origin == "externo" and incident.component == "correo"


def test_outbox_mailer_writes_eml(tmp_path):
    OutboxMailer(tmp_path, "Bosque Vivo <no@bv.local>").send(
        OutgoingEmail("a@b.co", "Asunto", "Cuerpo")
    )
    files = list(tmp_path.glob("*.eml"))
    assert len(files) == 1 and b"Subject: Asunto" in files[0].read_bytes()


@pytest.fixture
def api(client, db, mailer):
    client.app.dependency_overrides[get_mailer] = lambda: mailer
    AccountService(db, mailer, Settings()).create_user(EMAIL, "Auditora", PASSWORD)
    db.commit()
    return client


def test_auth_endpoints_require_admin_token(api):
    response = api.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert response.status_code == 401


def test_login_endpoint(api):
    ok = api.post("/api/v1/auth/login", headers=ADMIN, json={"email": EMAIL, "password": PASSWORD})
    assert ok.status_code == 200 and ok.json()["status"] == "ok"
    bad = api.post("/api/v1/auth/login", headers=ADMIN, json={"email": EMAIL, "password": "x"})
    assert bad.status_code == 401


def test_reset_endpoints_full_flow(api, mailer):
    unknown = api.post(
        "/api/v1/auth/password-reset", headers=ADMIN, json={"email": "otro@elpoli.edu.co"}
    )
    known = api.post("/api/v1/auth/password-reset", headers=ADMIN, json={"email": EMAIL})
    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()
    token = token_from(mailer.sent[0])
    verify = api.post("/api/v1/auth/password-reset/verify", headers=ADMIN, json={"token": token})
    assert verify.json()["status"] == "valido"
    weak = api.post(
        "/api/v1/auth/password-reset/confirm",
        headers=ADMIN,
        json={"token": token, "password": "corta"},
    )
    assert weak.status_code == 422
    done = api.post(
        "/api/v1/auth/password-reset/confirm",
        headers=ADMIN,
        json={"token": token, "password": "NuevaClave2026"},
    )
    assert done.status_code == 200
    reused = api.post(
        "/api/v1/auth/password-reset/confirm",
        headers=ADMIN,
        json={"token": token, "password": "OtraClave2026"},
    )
    assert reused.status_code == 410 and "ya se usó" in reused.json()["detail"]


class FakeSmtp:
    instances: list["FakeSmtp"] = []
    fail = False

    def __init__(self, host, port, timeout):
        self.host, self.port = host, port
        self.calls: list[str] = []
        FakeSmtp.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self, context):
        self.calls.append("starttls")

    def login(self, user, password):
        self.calls.append(f"login:{user}")

    def send_message(self, message):
        if FakeSmtp.fail:
            raise OSError("conexión rechazada")
        self.calls.append(f"send:{message['To']}")


def test_smtp_mailer_uses_tls_and_login(monkeypatch):
    monkeypatch.setattr("bosquevivo.accounts.mailer.smtplib.SMTP", FakeSmtp)
    settings = Settings(
        mail_backend="smtp", smtp_host="smtp.test", smtp_user="bv@test.co", smtp_password="x"
    )
    mailer = build_mailer(settings)
    assert isinstance(mailer, SmtpMailer)
    mailer.send(OutgoingEmail("a@b.co", "Asunto", "Cuerpo"))
    assert FakeSmtp.instances[-1].calls == ["starttls", "login:bv@test.co", "send:a@b.co"]
    FakeSmtp.fail = True
    with pytest.raises(ExternalServiceError):
        mailer.send(OutgoingEmail("a@b.co", "Asunto", "Cuerpo"))
    FakeSmtp.fail = False


def test_build_mailer_validates_configuration(tmp_path):
    assert isinstance(build_mailer(Settings(data_dir=tmp_path)), OutboxMailer)
    with pytest.raises(ValidationFailedError):
        build_mailer(Settings(mail_backend="smtp", smtp_host=""))
    with pytest.raises(ValidationFailedError):
        build_mailer(Settings(mail_backend="paloma"))
