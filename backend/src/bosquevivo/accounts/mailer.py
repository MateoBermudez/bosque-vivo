import smtplib
import ssl
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


@dataclass(frozen=True)
class OutgoingEmail:
    to: str
    subject: str
    body: str


class Mailer(Protocol):
    name: str

    def send(self, message: OutgoingEmail) -> None: ...


def _build(message: OutgoingEmail, sender: str) -> EmailMessage:
    email = EmailMessage()
    email["From"] = sender
    email["To"] = message.to
    email["Subject"] = message.subject
    email["Date"] = format_datetime(datetime.now(UTC))
    email["Message-ID"] = make_msgid(domain="bosquevivo.local")
    email.set_content(message.body)
    return email


class OutboxMailer:
    name = "outbox"

    def __init__(self, directory: Path, sender: str) -> None:
        self.directory = directory
        self.sender = sender

    def send(self, message: OutgoingEmail) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        path = self.directory / f"{stamp}.eml"
        path.write_bytes(bytes(_build(message, self.sender)))
        log.info("mail_saved_to_outbox", file=path.name)


class SmtpMailer:
    name = "smtp"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, message: OutgoingEmail) -> None:
        settings = self.settings
        email = _build(message, settings.mail_from)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_starttls:
                    server.starttls(context=ssl.create_default_context())
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(email)
        except (OSError, smtplib.SMTPException) as exc:
            raise ExternalServiceError(f"no se pudo enviar el correo: {exc}") from exc
        log.info("mail_sent", backend="smtp")


class MemoryMailer:
    name = "memory"

    def __init__(self) -> None:
        self.sent: list[OutgoingEmail] = []

    def send(self, message: OutgoingEmail) -> None:
        self.sent.append(message)


def build_mailer(settings: Settings) -> Mailer:
    backend = settings.mail_backend.strip().lower()
    if backend == "smtp":
        if not settings.smtp_host:
            raise ValidationFailedError("MAIL_BACKEND=smtp requiere SMTP_HOST")
        return SmtpMailer(settings)
    if backend == "outbox":
        return OutboxMailer(settings.outbox_dir, settings.mail_from)
    raise ValidationFailedError(f"MAIL_BACKEND desconocido: {settings.mail_backend}")
