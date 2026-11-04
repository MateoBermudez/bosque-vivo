import re
import smtplib
from datetime import timedelta

import pytest

from bosquevivo.accounts import (
    AccountService,
    ChallengeError,
    MemoryMailer,
    OutgoingEmail,
    SmtpMailer,
    TokenStatus,
    build_mailer,
)
from bosquevivo.accounts.mailer import build_message, resolved_backend, smtp_endpoint
from bosquevivo.accounts.service import mask_email
from bosquevivo.api.routers.auth import get_mailer
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.db.base import utcnow
from bosquevivo.db.models import Incident

ADMIN = {"X-Admin-Token": "secreto"}
EMAIL = "auditor@elpoli.edu.co"
PASSWORD = "BosqueVivo2026"


class Clock:
    def __init__(self) -> None:
        self.now = utcnow()

    def __call__(self):
        return self.now

    def advance(self, minutes: int) -> None:
        self.now += timedelta(minutes=minutes)


def code_from(mail: OutgoingEmail) -> str:
    match = re.search(r"Código: (\d{6})", mail.body)
    assert match
    return match.group(1)


def link_from(mail: OutgoingEmail) -> str:
    match = re.search(r"token=([\w-]+)", mail.body)
    assert match
    return match.group(1)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def mailer():
    return MemoryMailer()


def make_service(db, mailer, clock, **overrides) -> AccountService:
    settings = Settings(
        web_base_url="https://bosque.test", **{"auth_two_factor": "on", **overrides}
    )
    return AccountService(db, mailer, settings, clock)


@pytest.fixture
def service(db, mailer, clock):
    accounts = make_service(db, mailer, clock)
    accounts.create_user(EMAIL, "Auditor", PASSWORD)
    return accounts


def test_login_sends_code_and_verifies(service, mailer):
    step = service.start_login(EMAIL, PASSWORD, "Chrome · 10.0.0.1")
    assert step.needs_code and step.destination == "au*****@elpoli.edu.co"
    mail = mailer.sent[-1]
    assert mail.to == EMAIL and "código de verificación" in mail.subject
    assert mail.html and "<html" in mail.html
    assert step.challenge
    user = service.verify_login(step.challenge, code_from(mail))
    assert user is not None and user.email == EMAIL
    alert = mailer.sent[-1]
    assert "nuevo inicio de sesión" in alert.subject and "Chrome · 10.0.0.1" in alert.body


def test_wrong_password_does_not_send_code(service, mailer):
    assert not service.start_login(EMAIL, "otra-clave-123").needs_code
    assert mailer.sent == []


def test_wrong_code_counts_attempts_until_exhausted(service, mailer):
    step = service.start_login(EMAIL, PASSWORD)
    assert step.challenge
    real = code_from(mailer.sent[-1])
    wrong = "000000" if real != "000000" else "111111"
    for _ in range(4):
        assert service.verify_login(step.challenge, wrong) is None
    with pytest.raises(ChallengeError, match="Demasiados intentos"):
        service.verify_login(step.challenge, wrong)
    with pytest.raises(ChallengeError):
        service.verify_login(step.challenge, real)


def test_code_expires_and_is_single_use(service, mailer, clock):
    step = service.start_login(EMAIL, PASSWORD)
    assert step.challenge
    code = code_from(mailer.sent[-1])
    clock.advance(11)
    with pytest.raises(ChallengeError, match="venció"):
        service.verify_login(step.challenge, code)
    step = service.start_login(EMAIL, PASSWORD)
    assert step.challenge
    code = code_from(mailer.sent[-1])
    assert service.verify_login(step.challenge, code) is not None
    with pytest.raises(ChallengeError, match="no es válida"):
        service.verify_login(step.challenge, code)


def test_resend_replaces_code_with_limit(service, mailer):
    step = service.start_login(EMAIL, PASSWORD)
    assert step.challenge
    first = code_from(mailer.sent[-1])
    service.resend_code(step.challenge)
    second = code_from(mailer.sent[-1])
    if first != second:
        assert service.verify_login(step.challenge, first) is None
    service.resend_code(step.challenge)
    with pytest.raises(ChallengeError):
        service.resend_code(step.challenge)
    assert service.verify_login(step.challenge, code_from(mailer.sent[-1])) is not None


def test_two_factor_can_be_disabled(db, mailer, clock):
    accounts = make_service(db, mailer, clock, auth_two_factor="off", auth_login_alerts=False)
    accounts.create_user(EMAIL, "Auditor", PASSWORD)
    step = accounts.start_login(EMAIL, PASSWORD)
    assert step.user is not None and not step.needs_code
    assert mailer.sent == []


def test_lock_sends_security_email(service, mailer):
    for _ in range(5):
        service.authenticate(EMAIL, "incorrecta-123")
    assert "bloqueamos" in mailer.sent[-1].subject.lower()


def test_password_change_notifies(service, mailer):
    service.request_reset(EMAIL)
    service.confirm_reset(link_from(mailer.sent[-1]), "NuevaClave2026")
    assert "tu contraseña cambió" in mailer.sent[-1].subject


def test_invitation_sets_first_password(db, mailer, clock):
    accounts = make_service(db, mailer, clock, invitation_ttl_hours=72)
    user, link = accounts.invite_user("nueva@elpoli.edu.co", "Nueva")
    invitation = mailer.sent[-1]
    assert "activa tu cuenta" in invitation.subject and "72 horas" in invitation.body
    assert not accounts.authenticate("nueva@elpoli.edu.co", user.password_hash).user
    token = link_from(invitation)
    assert link.endswith(token)
    assert accounts.token_purpose(token) == "invitacion"
    accounts.confirm_reset(token, "PrimeraClave2026")
    assert accounts.authenticate("nueva@elpoli.edu.co", "PrimeraClave2026").user is not None
    assert all("cambió" not in mail.subject for mail in mailer.sent)
    clock.advance(73 * 60)
    assert accounts.token_status(token) is TokenStatus.USED


def test_code_mail_failure_is_reported(db, clock):
    class Broken:
        name = "roto"

        def send(self, message):
            raise ExternalServiceError("smtp caído")

    accounts = make_service(db, Broken(), clock)
    accounts.create_user(EMAIL, "Auditor", PASSWORD)
    with pytest.raises(ExternalServiceError):
        accounts.start_login(EMAIL, PASSWORD)
    assert db.query(Incident).filter(Incident.component == "correo").count() == 1


def test_mask_email():
    assert mask_email("auditor@elpoli.edu.co") == "au*****@elpoli.edu.co"
    assert mask_email("ab@x.co") == "a***@x.co"


def test_smtp_presets_and_auto_backend(tmp_path):
    gmail = Settings(smtp_user="equipo@gmail.com", smtp_password="app", data_dir=tmp_path)
    assert smtp_endpoint(gmail) == ("smtp.gmail.com", 587)
    assert resolved_backend(gmail) == "smtp"
    assert isinstance(build_mailer(gmail), SmtpMailer)
    assert resolved_backend(Settings(data_dir=tmp_path)) == "outbox"
    custom = Settings(smtp_host="mail.test", smtp_port=465, smtp_user="a@b.co")
    assert smtp_endpoint(custom) == ("mail.test", 465)


def test_message_has_text_and_html():
    message = build_message(
        OutgoingEmail("a@b.co", "Asunto", "Texto", "<p>Hola</p>"), "BV <x@y.co>"
    )
    types = [part.get_content_type() for part in message.iter_parts()]
    assert types == ["text/plain", "text/html"]


class FlakySmtp:
    calls = 0

    def __init__(self, host, port, timeout):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self, context):
        pass

    def login(self, user, password):
        if password == "mala":
            raise smtplib.SMTPAuthenticationError(535, b"bad")

    def send_message(self, message):
        FlakySmtp.calls += 1
        if FlakySmtp.calls == 1:
            raise OSError("reset")


def test_smtp_retries_and_explains_auth_errors():
    settings = Settings(smtp_user="equipo@gmail.com", smtp_password="buena")
    mailer = SmtpMailer(settings, connect=FlakySmtp, sleep=lambda _: None)
    mailer.send(OutgoingEmail("a@b.co", "Asunto", "Cuerpo"))
    assert FlakySmtp.calls == 2
    bad = SmtpMailer(
        Settings(smtp_user="equipo@gmail.com", smtp_password="mala"),
        connect=FlakySmtp,
        sleep=lambda _: None,
    )
    with pytest.raises(ExternalServiceError, match="contraseña de aplicación"):
        bad.send(OutgoingEmail("a@b.co", "Asunto", "Cuerpo"))


@pytest.fixture
def api(client, db, mailer):
    client.app.dependency_overrides[get_mailer] = lambda: mailer
    client.app.dependency_overrides[get_settings] = lambda: Settings(
        admin_token="secreto", auth_two_factor="on"
    )
    AccountService(db, mailer, Settings()).create_user(EMAIL, "Auditor", PASSWORD)
    db.commit()
    return client


def test_two_factor_endpoints(api, mailer):
    first = api.post(
        "/api/v1/auth/login",
        headers=ADMIN,
        json={"email": EMAIL, "password": PASSWORD, "client": "Firefox"},
    ).json()
    assert first["status"] == "codigo" and first["destination"].endswith("@elpoli.edu.co")
    wrong = api.post(
        "/api/v1/auth/login/verify",
        headers=ADMIN,
        json={"challenge": first["challenge"], "code": "000000"},
    )
    assert wrong.status_code in {200, 401}
    resent = api.post(
        "/api/v1/auth/login/resend", headers=ADMIN, json={"challenge": first["challenge"]}
    )
    assert resent.status_code == 200
    done = api.post(
        "/api/v1/auth/login/verify",
        headers=ADMIN,
        json={"challenge": first["challenge"], "code": code_from(mailer.sent[-1])},
    )
    assert done.status_code == 200 and done.json()["email"] == EMAIL
    reused = api.post(
        "/api/v1/auth/login/verify",
        headers=ADMIN,
        json={"challenge": first["challenge"], "code": "123456"},
    )
    assert reused.status_code == 410


def test_verify_reports_purpose(api, mailer):
    api.post("/api/v1/auth/password-reset", headers=ADMIN, json={"email": EMAIL})
    token = link_from(mailer.sent[-1])
    body = api.post(
        "/api/v1/auth/password-reset/verify", headers=ADMIN, json={"token": token}
    ).json()
    assert body == {"status": "valido", "detail": None, "purpose": "reset"}


def test_auto_two_factor_follows_smtp(db, mailer, clock):
    accounts = make_service(db, mailer, clock, auth_two_factor="auto")
    accounts.create_user(EMAIL, "Auditor", PASSWORD)
    assert not accounts.two_factor_enabled()
    mailer.name = "smtp"
    assert accounts.two_factor_enabled()
