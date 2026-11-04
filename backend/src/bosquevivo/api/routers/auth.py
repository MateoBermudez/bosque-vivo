from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from bosquevivo.accounts import AccountService, ChallengeError, Mailer, ResetError, build_mailer
from bosquevivo.api.deps import db_session, require_admin
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.core.errors import ExternalServiceError, ValidationFailedError

router = APIRouter(
    prefix="/api/v1/auth", tags=["autenticación"], dependencies=[Depends(require_admin)]
)

MAIL_UNAVAILABLE = (
    "No pudimos enviar el código de verificación por correo. Intenta de nuevo en unos minutos."
)


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)
    client: str = Field(default="", max_length=200)


class LoginOut(BaseModel):
    status: str
    email: str | None = None
    name: str | None = None
    challenge: str | None = None
    destination: str | None = None


class VerifyIn(BaseModel):
    challenge: str = Field(max_length=200)
    code: str = Field(max_length=12)


class ResendIn(BaseModel):
    challenge: str = Field(max_length=200)


class ResetRequestIn(BaseModel):
    email: str = Field(max_length=254)


class TokenIn(BaseModel):
    token: str = Field(max_length=200)


class ResetConfirmIn(BaseModel):
    token: str = Field(max_length=200)
    password: str = Field(max_length=256)


class MessageOut(BaseModel):
    detail: str


class TokenStatusOut(BaseModel):
    status: str
    detail: str | None
    purpose: str


def get_mailer(settings: Settings = Depends(get_settings)) -> Mailer:
    return build_mailer(settings)


def account_service(
    session: Session = Depends(db_session),
    mailer: Mailer = Depends(get_mailer),
    settings: Settings = Depends(get_settings),
) -> AccountService:
    return AccountService(session, mailer, settings)


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, service: AccountService = Depends(account_service)):
    try:
        step = service.start_login(body.email, body.password, body.client)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=503, detail=MAIL_UNAVAILABLE) from exc
    if step.locked:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.",
        )
    if step.needs_code:
        return LoginOut(status="codigo", challenge=step.challenge, destination=step.destination)
    if step.user is None:
        raise HTTPException(status_code=401, detail="El correo o la contraseña no son correctos.")
    return LoginOut(status="ok", email=step.user.email, name=step.user.name)


@router.post("/login/verify", response_model=LoginOut)
def verify_login(body: VerifyIn, service: AccountService = Depends(account_service)):
    try:
        user = service.verify_login(body.challenge, body.code)
    except ChallengeError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    if user is None:
        raise HTTPException(status_code=401, detail="El código no es correcto.")
    return LoginOut(status="ok", email=user.email, name=user.name)


@router.post("/login/resend", response_model=LoginOut)
def resend_code(body: ResendIn, service: AccountService = Depends(account_service)):
    try:
        destination = service.resend_code(body.challenge)
    except ChallengeError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=503, detail=MAIL_UNAVAILABLE) from exc
    return LoginOut(status="codigo", challenge=body.challenge, destination=destination)


@router.post("/password-reset", response_model=MessageOut, status_code=202)
def request_reset(body: ResetRequestIn, service: AccountService = Depends(account_service)):
    return MessageOut(detail=service.request_reset(body.email))


@router.post("/password-reset/verify", response_model=TokenStatusOut)
def verify_token(body: TokenIn, service: AccountService = Depends(account_service)):
    status = service.token_status(body.token)
    message = None if status == "valido" else ResetError(status).args[0]
    return TokenStatusOut(
        status=status.value, detail=message, purpose=service.token_purpose(body.token)
    )


@router.post("/password-reset/confirm", response_model=MessageOut)
def confirm_reset(body: ResetConfirmIn, service: AccountService = Depends(account_service)):
    try:
        service.confirm_reset(body.token, body.password)
    except ResetError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except ValidationFailedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return MessageOut(detail="Tu contraseña quedó guardada. Ya puedes iniciar sesión.")
