import hmac
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.accounts import templates
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
from bosquevivo.db.models import AuditorUser, LoginChallenge, PasswordResetToken

log = get_logger(__name__)

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 10
MAX_RESETS_PER_HOUR = 3
MAX_CODE_ATTEMPTS = 5
MAX_CODE_SENDS = 3
PURPOSE_RESET = "reset"
PURPOSE_INVITATION = "invitacion"
UNUSABLE_PREFIX = "!"

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


class ChallengeStatus(StrEnum):
    VALID = "valido"
    INVALID = "invalido"
    EXPIRED = "vencido"
    EXHAUSTED = "agotado"


CHALLENGE_MESSAGES = {
    ChallengeStatus.INVALID: "La verificación no es válida. Inicia sesión de nuevo.",
    ChallengeStatus.EXPIRED: "El código venció. Inicia sesión de nuevo para recibir otro.",
    ChallengeStatus.EXHAUSTED: "Demasiados intentos con el código. Inicia sesión de nuevo.",
}


class ChallengeError(ValidationFailedError):
    def __init__(self, status: ChallengeStatus) -> None:
        super().__init__(CHALLENGE_MESSAGES[status])
        self.status = status


@dataclass(frozen=True)
class LoginOutcome:
    user: AuditorUser | None
    locked: bool = False


@dataclass(frozen=True)
class LoginStep:
    user: AuditorUser | None = None
    locked: bool = False
    challenge: str | None = None
    destination: str | None = None

    @property
    def needs_code(self) -> bool:
        return self.challenge is not None


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    visible = local[:2] if len(local) > 3 else local[:1]
    return f"{visible}{'*' * max(3, len(local) - len(visible))}@{domain}"


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


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

    def _new_user(self, email: str, name: str, password_hash: str) -> AuditorUser:
        address = normalize_email(email)
        if not is_valid_email(address):
            raise ValidationFailedError("el correo no es válido")
        if self.find(address):
            raise ValidationFailedError("ya existe un usuario con ese correo")
        user = AuditorUser(
            email=address,
            name=name.strip() or address,
            password_hash=password_hash,
            password_changed_at=self.clock(),
        )
        self.session.add(user)
        self.session.flush()
        log.info("auditor_created", user_id=user.id)
        return user

    def create_user(self, email: str, name: str, password: str) -> AuditorUser:
        self._check_password(password, normalize_email(email))
        return self._new_user(email, name, hash_password(password))

    def invite_user(self, email: str, name: str) -> tuple[AuditorUser, str]:
        user = self._new_user(email, name, UNUSABLE_PREFIX + new_token())
        hours = self.settings.invitation_ttl_hours
        link = self._link(self._issue_token(user, PURPOSE_INVITATION, timedelta(hours=hours)))
        self._notify(
            templates.invitation_email(user.email, user.name, link, hours, site=self._site)
        )
        return user, link

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
                self._notify(
                    templates.account_locked_email(
                        user.email, user.name, LOCK_MINUTES, site=self._site
                    )
                )
            self.session.flush()
            return LoginOutcome(None)
        user.failed_logins = 0
        user.locked_until = None
        self.session.flush()
        return LoginOutcome(user)

    def two_factor_enabled(self) -> bool:
        mode = self.settings.auth_two_factor.strip().lower()
        if mode in {"on", "true", "1", "si", "sí"}:
            return True
        if mode in {"off", "false", "0", "no"}:
            return False
        return self.mailer.name == "smtp"

    def start_login(self, email: str, password: str, client: str = "") -> LoginStep:
        outcome = self.authenticate(email, password)
        if outcome.user is None:
            return LoginStep(locked=outcome.locked)
        user = outcome.user
        if not self.two_factor_enabled():
            self.complete_login(user, client)
            return LoginStep(user=user)
        raw = new_token()
        code = new_code()
        challenge = LoginChallenge(
            user_id=user.id,
            token_hash=token_digest(raw),
            code_hash=token_digest(f"{raw}:{code}"),
            client=client[:200],
            expires_at=self.clock() + timedelta(minutes=self.settings.auth_code_ttl_minutes),
            created_at=self.clock(),
        )
        self.session.add(challenge)
        self.session.flush()
        self._send(
            templates.login_code_email(
                user.email, user.name, code, self.settings.auth_code_ttl_minutes, site=self._site
            )
        )
        return LoginStep(challenge=raw, destination=mask_email(user.email))

    def _challenge(self, raw: str) -> LoginChallenge:
        challenge = (
            self.session.scalars(
                select(LoginChallenge).where(LoginChallenge.token_hash == token_digest(raw))
            ).first()
            if raw and len(raw) <= 200
            else None
        )
        if challenge is None or challenge.used_at is not None or not challenge.user.active:
            raise ChallengeError(ChallengeStatus.INVALID)
        if as_aware(challenge.expires_at) <= self.clock():
            raise ChallengeError(ChallengeStatus.EXPIRED)
        if challenge.attempts >= MAX_CODE_ATTEMPTS:
            raise ChallengeError(ChallengeStatus.EXHAUSTED)
        return challenge

    def verify_login(self, raw: str, code: str) -> AuditorUser | None:
        challenge = self._challenge(raw)
        expected = token_digest(f"{raw}:{code.strip()}")
        if not hmac.compare_digest(expected, challenge.code_hash):
            challenge.attempts += 1
            self.session.flush()
            if challenge.attempts >= MAX_CODE_ATTEMPTS:
                raise ChallengeError(ChallengeStatus.EXHAUSTED)
            return None
        challenge.used_at = self.clock()
        self.session.flush()
        self.complete_login(challenge.user, challenge.client)
        return challenge.user

    def resend_code(self, raw: str) -> str:
        challenge = self._challenge(raw)
        if challenge.sends >= MAX_CODE_SENDS:
            raise ChallengeError(ChallengeStatus.EXHAUSTED)
        code = new_code()
        challenge.code_hash = token_digest(f"{raw}:{code}")
        challenge.sends += 1
        challenge.attempts = 0
        challenge.expires_at = self.clock() + timedelta(minutes=self.settings.auth_code_ttl_minutes)
        self.session.flush()
        user = challenge.user
        self._send(
            templates.login_code_email(
                user.email, user.name, code, self.settings.auth_code_ttl_minutes, site=self._site
            )
        )
        return mask_email(user.email)

    def complete_login(self, user: AuditorUser, client: str = "") -> None:
        log.info("auditor_signed_in", user_id=user.id)
        if self.settings.auth_login_alerts:
            self._notify(
                templates.new_login_email(
                    user.email,
                    user.name,
                    self.clock(),
                    client or "no informado",
                    site=self._site,
                )
            )

    def request_reset(self, email: str) -> str:
        user = self.find(email)
        if user is None or not user.active:
            log.info("password_reset_requested", known=False)
            return GENERIC_RESET_MESSAGE
        now = self.clock()
        since = now - timedelta(hours=1)
        recent = [
            token
            for token in self.session.scalars(
                select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
            ).all()
            if as_aware(token.created_at) > since
        ]
        if len(recent) >= MAX_RESETS_PER_HOUR:
            log.warning("password_reset_throttled", user_id=user.id)
            return GENERIC_RESET_MESSAGE
        minutes = self.settings.password_reset_ttl_minutes
        raw = self._issue_token(user, PURPOSE_RESET, timedelta(minutes=minutes))
        self._notify(
            templates.reset_email(user.email, user.name, self._link(raw), minutes, site=self._site)
        )
        log.info("password_reset_requested", known=True, user_id=user.id)
        return GENERIC_RESET_MESSAGE

    def _open_tokens(self, user: AuditorUser) -> list[PasswordResetToken]:
        return list(
            self.session.scalars(
                select(PasswordResetToken).where(
                    PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
                )
            ).all()
        )

    def _issue_token(self, user: AuditorUser, purpose: str, ttl: timedelta) -> str:
        now = self.clock()
        for token in self._open_tokens(user):
            token.used_at = now
        raw = new_token()
        self.session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_digest(raw),
                purpose=purpose,
                expires_at=now + ttl,
                created_at=now,
            )
        )
        self.session.flush()
        return raw

    @property
    def _site(self) -> str:
        return self.settings.web_base_url

    def _link(self, raw: str) -> str:
        return f"{self.settings.web_base_url.rstrip('/')}/acceso/restablecer?token={raw}"

    def _send(self, message: OutgoingEmail) -> None:
        try:
            self.mailer.send(message)
        except ExternalServiceError as exc:
            record_incident(self.session, "correo", exc)
            raise

    def _notify(self, message: OutgoingEmail) -> None:
        try:
            self._send(message)
        except ExternalServiceError:
            log.warning("mail_not_sent", subject=message.subject)

    def _token(self, raw: str) -> PasswordResetToken | None:
        if not raw or len(raw) > 200:
            return None
        return self.session.scalars(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_digest(raw))
        ).first()

    def token_purpose(self, raw: str) -> str:
        token = self._token(raw)
        return token.purpose if token else PURPOSE_RESET

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
        token.used_at = now
        for item in self._open_tokens(user):
            item.used_at = now
        self.session.flush()
        log.info("password_reset_completed", user_id=user.id, purpose=token.purpose)
        if token.purpose == PURPOSE_RESET:
            self._notify(
                templates.password_changed_email(user.email, user.name, now, site=self._site)
            )
        return user

    def send_test(self, to: str) -> None:
        self._send(templates.test_email(normalize_email(to), site=self._site))

    def _check_password(self, password: str, email: str) -> None:
        problems = password_problems(password, email)
        if problems:
            raise ValidationFailedError("La contraseña " + "; ".join(problems) + ".")
