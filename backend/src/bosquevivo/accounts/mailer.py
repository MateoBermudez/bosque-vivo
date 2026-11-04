import smtplib
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path
from typing import Protocol

from bosquevivo.core.config import Settings
from bosquevivo.core.errors import ExternalServiceError, ValidationFailedError
from bosquevivo.core.logging import get_logger

log = get_logger(__name__)

SMTP_PRESETS: dict[str, tuple[str, int]] = {
    "gmail.com": ("smtp.gmail.com", 587),
    "googlemail.com": ("smtp.gmail.com", 587),
    "elpoli.edu.co": ("smtp.gmail.com", 587),
    "outlook.com": ("smtp.office365.com", 587),
    "hotmail.com": ("smtp.office365.com", 587),
    "live.com": ("smtp.office365.com", 587),
    "yahoo.com": ("smtp.mail.yahoo.com", 587),
}
SEND_ATTEMPTS = 2


@dataclass(frozen=True)
class OutgoingEmail:
    to: str
    subject: str
    body: str
    html: str | None = None


class Mailer(Protocol):
    name: str

    def send(self, message: OutgoingEmail) -> None: ...


def build_message(message: OutgoingEmail, sender: str) -> EmailMessage:
    email = EmailMessage()
    email["From"] = sender
    email["To"] = message.to
    email["Subject"] = message.subject
    email["Date"] = format_datetime(datetime.now(UTC))
    email["Message-ID"] = make_msgid(domain="bosquevivo.local")
    email.set_content(message.body)
    if message.html:
        email.add_alternative(message.html, subtype="html")
    return email


def smtp_endpoint(settings: Settings) -> tuple[str, int]:
    if settings.smtp_host:
        return settings.smtp_host, settings.smtp_port
    domain = settings.smtp_user.rpartition("@")[2].lower()
    if domain in SMTP_PRESETS:
        return SMTP_PRESETS[domain]
    return "", settings.smtp_port


def sender_address(settings: Settings) -> str:
    if settings.mail_from:
        return settings.mail_from
    if settings.smtp_user:
        return f"Bosque Vivo <{settings.smtp_user}>"
    return "Bosque Vivo <no-responder@bosquevivo.local>"


class OutboxMailer:
    name = "outbox"

    def __init__(self, directory: Path, sender: str) -> None:
        self.directory = directory
        self.sender = sender

    def send(self, message: OutgoingEmail) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        path = self.directory / f"{stamp}.eml"
        path.write_bytes(bytes(build_message(message, self.sender)))
        log.info("mail_saved_to_outbox", file=path.name)


class SmtpMailer:
    name = "smtp"

    def __init__(
        self,
        settings: Settings,
        connect: Callable[..., smtplib.SMTP] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self.host, self.port = smtp_endpoint(settings)
        self.sender = sender_address(settings)
        self.connect = connect
        self.sleep = sleep

    def _open(self) -> smtplib.SMTP:
        if self.connect is not None:
            return self.connect(self.host, self.port, timeout=20)
        if self.settings.smtp_ssl or self.port == 465:
            return smtplib.SMTP_SSL(
                self.host, self.port, timeout=20, context=ssl.create_default_context()
            )
        return smtplib.SMTP(self.host, self.port, timeout=20)

    def _deliver(self, email: EmailMessage) -> None:
        settings = self.settings
        with self._open() as server:
            if settings.smtp_starttls and not (settings.smtp_ssl or self.port == 465):
                server.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(email)

    def send(self, message: OutgoingEmail) -> None:
        email = build_message(message, self.sender)
        last_error: Exception | None = None
        for attempt in range(1, SEND_ATTEMPTS + 1):
            try:
                self._deliver(email)
                log.info("mail_sent", backend="smtp", attempt=attempt)
                return
            except smtplib.SMTPAuthenticationError as exc:
                raise ExternalServiceError(
                    "el servidor SMTP rechazó el usuario o la contraseña (en Gmail use una "
                    "contraseña de aplicación)"
                ) from exc
            except (OSError, smtplib.SMTPException) as exc:
                last_error = exc
                log.warning("mail_retry", attempt=attempt, error=str(exc))
                if attempt < SEND_ATTEMPTS:
                    self.sleep(1.0)
        raise ExternalServiceError(f"no se pudo enviar el correo: {last_error}")


class MemoryMailer:
    name = "memory"

    def __init__(self) -> None:
        self.sent: list[OutgoingEmail] = []

    def send(self, message: OutgoingEmail) -> None:
        self.sent.append(message)


def resolved_backend(settings: Settings) -> str:
    backend = settings.mail_backend.strip().lower()
    if backend == "auto":
        host, _ = smtp_endpoint(settings)
        return "smtp" if host and settings.smtp_user and settings.smtp_password else "outbox"
    return backend


def build_mailer(settings: Settings) -> Mailer:
    backend = resolved_backend(settings)
    if backend == "smtp":
        host, _ = smtp_endpoint(settings)
        if not host:
            raise ValidationFailedError(
                "MAIL_BACKEND=smtp requiere SMTP_HOST (o un SMTP_USER de Gmail u Outlook)"
            )
        return SmtpMailer(settings)
    if backend == "outbox":
        return OutboxMailer(settings.outbox_dir, sender_address(settings))
    raise ValidationFailedError(f"MAIL_BACKEND desconocido: {settings.mail_backend}")
