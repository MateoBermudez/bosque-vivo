from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.accounts.mailer import Mailer, OutgoingEmail
from bosquevivo.accounts.passwords import (
    DUMMY_HASH,
    hash_password,
    is_valid_email,
    new_token,
    normalize_email,
    password_problems,
    token_digest,
    verify_password,
)
from bosquevivo.core.config import Settings
from bosquevivo.core.errors import ExternalServiceError, ValidationFailedError
from bosquevivo.core.incidents import as_aware, record_incident
from bosquevivo.core.logging import get_logger
from bosquevivo.db.base import utcnow
from bosquevivo.db.models import AuditorUser, PasswordResetToken

log = get_logger(__name__)

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 10
MAX_RESETS_PER_HOUR = 3

GENERIC_RESET_MESSAGE = (
    "Si la dirección está registrada, recibirás un correo con las instrucciones para "
    "restablecer tu contraseña."
)


class TokenStatus(StrEnum):
    VALID = "valido"
    INVALID = "invalido"
    EXPIRED = "expirado"
    USED = "usado"


TOKEN_MESSAGES = {
    TokenStatus.INVALID: "El enlace no es válido. Solicita uno nuevo.",
    TokenStatus.EXPIRED: "El enlace venció. Solicita uno nuevo.",
    TokenStatus.USED: "El enlace ya se usó. Solicita uno nuevo si lo necesitas.",
}


class ResetError(ValidationFailedError):
    def __init__(self, status: TokenStatus) -> None:
        super().__init__(TOKEN_MESSAGES[status])
        self.status = status


@dataclass(frozen=True)
class LoginOutcome:
    user: AuditorUser | None
    locked: bool = False


class AccountService:
    def __init__(
        self,
        session: Session,
        mailer: Mailer,
        settings: Settings,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self.session = session
        self.mailer = mailer
        self.settings = settings
        self.clock = clock

    def find(self, email: str) -> AuditorUser | None:
        return self.session.scalars(
            select(AuditorUser).where(AuditorUser.email == normalize_email(email))
        ).first()

    def create_user(self, email: str, name: str, password: str) -> AuditorUser:
        address = normalize_email(email)
        if not is_valid_email(address):
            raise ValidationFailedError("el correo no es válido")
        if self.find(address):
            raise ValidationFailedError("ya existe un usuario con ese correo")
        self._check_password(password, address)
        user = AuditorUser(
            email=address,
            name=name.strip() or address,
            password_hash=hash_password(password),
            password_changed_at=self.clock(),
        )
        self.session.add(user)
        self.session.flush()
        log.info("auditor_created", user_id=user.id)
        return user

    def set_active(self, email: str, active: bool) -> AuditorUser:
        user = self.find(email)
        if not user:
            raise ValidationFailedError("no existe un usuario con ese correo")
        user.active = active
        self.session.flush()
        return user

    def list_users(self) -> list[AuditorUser]:
        return list(self.session.scalars(select(AuditorUser).order_by(AuditorUser.email)).all())

    def authenticate(self, email: str, password: str) -> LoginOutcome:
        user = self.find(email)
        if user is None or not user.active:
            verify_password(password, DUMMY_HASH)
            return LoginOutcome(None)
        now = self.clock()
        if user.locked_until and as_aware(user.locked_until) > now:
            return LoginOutcome(None, locked=True)
        if not verify_password(password, user.password_hash):
            user.failed_logins += 1
            if user.failed_logins >= MAX_FAILED_LOGINS:
                user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
                user.failed_logins = 0
                log.warning("auditor_locked", user_id=user.id)
            self.session.flush()
            return LoginOutcome(None)
        user.failed_logins = 0
        user.locked_until = None
        self.session.flush()
        return LoginOutcome(user)

    def request_reset(self, email: str) -> str:
        user = self.find(email)
        if user is None or not user.active:
            log.info("password_reset_requested", known=False)
            return GENERIC_RESET_MESSAGE
        now = self.clock()
        recent = [
            token
            for token in user.reset_tokens
            if as_aware(token.created_at) > now - timedelta(hours=1)
        ]
        if len(recent) >= MAX_RESETS_PER_HOUR:
            log.warning("password_reset_throttled", user_id=user.id)
            return GENERIC_RESET_MESSAGE
        for token in user.reset_tokens:
            if token.used_at is None:
                token.used_at = now
        raw = new_token()
        minutes = self.settings.password_reset_ttl_minutes
        self.session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_digest(raw),
                expires_at=now + timedelta(minutes=minutes),
                created_at=now,
            )
        )
        self.session.flush()
        try:
            self.mailer.send(self._reset_email(user, raw, minutes))
        except ExternalServiceError as exc:
            record_incident(self.session, "correo", exc)
        log.info("password_reset_requested", known=True, user_id=user.id)
        return GENERIC_RESET_MESSAGE

    def _reset_email(self, user: AuditorUser, raw: str, minutes: int) -> OutgoingEmail:
        link = f"{self.settings.web_base_url.rstrip('/')}/acceso/restablecer?token={raw}"
        body = (
            f"Hola, {user.name}.\n\n"
            "Recibimos una solicitud para restablecer la contraseña de tu cuenta de auditor en "
            "Bosque Vivo.\n\n"
            f"Abre este enlace para elegir una nueva contraseña:\n{link}\n\n"
            f"El enlace vence en {minutes} minutos y solo se puede usar una vez.\n\n"
            "Si no hiciste esta solicitud, ignora este correo: tu contraseña no cambiará.\n"
        )
        return OutgoingEmail(
            to=user.email, subject="Bosque Vivo: restablecer tu contraseña", body=body
        )

    def _token(self, raw: str) -> PasswordResetToken | None:
        if not raw or len(raw) > 200:
            return None
        return self.session.scalars(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_digest(raw))
        ).first()

    def token_status(self, raw: str) -> TokenStatus:
        token = self._token(raw)
        if token is None or not token.user.active:
            return TokenStatus.INVALID
        if token.used_at is not None:
            return TokenStatus.USED
        if as_aware(token.expires_at) <= self.clock():
            return TokenStatus.EXPIRED
        return TokenStatus.VALID

    def confirm_reset(self, raw: str, new_password: str) -> AuditorUser:
        status = self.token_status(raw)
        if status is not TokenStatus.VALID:
            raise ResetError(status)
        token = self._token(raw)
        assert token is not None
        user = token.user
        self._check_password(new_password, user.email)
        now = self.clock()
        user.password_hash = hash_password(new_password)
        user.password_changed_at = now
        user.failed_logins = 0
        user.locked_until = None
        for item in user.reset_tokens:
            if item.used_at is None:
                item.used_at = now
        self.session.flush()
        log.info("password_reset_completed", user_id=user.id)
        return user

    def _check_password(self, password: str, email: str) -> None:
        problems = password_problems(password, email)
        if problems:
            raise ValidationFailedError("La contraseña " + "; ".join(problems) + ".")
