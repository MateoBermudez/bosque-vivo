from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from bosquevivo.accounts import AccountService, Mailer, ResetError, build_mailer
from bosquevivo.api.deps import db_session, require_admin
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.core.errors import ValidationFailedError

router = APIRouter(
    prefix="/api/v1/auth", tags=["autenticación"], dependencies=[Depends(require_admin)]
)


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


class UserOut(BaseModel):
    email: str
    name: str


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


def get_mailer(settings: Settings = Depends(get_settings)) -> Mailer:
    return build_mailer(settings)


def account_service(
    session: Session = Depends(db_session),
    mailer: Mailer = Depends(get_mailer),
    settings: Settings = Depends(get_settings),
) -> AccountService:
    return AccountService(session, mailer, settings)


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, service: AccountService = Depends(account_service)):
    outcome = service.authenticate(body.email, body.password)
    if outcome.locked:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.",
        )
    if outcome.user is None:
        raise HTTPException(status_code=401, detail="El correo o la contraseña no son correctos.")
    return UserOut(email=outcome.user.email, name=outcome.user.name)


@router.post("/password-reset", response_model=MessageOut, status_code=202)
def request_reset(body: ResetRequestIn, service: AccountService = Depends(account_service)):
    return MessageOut(detail=service.request_reset(body.email))


@router.post("/password-reset/verify", response_model=TokenStatusOut)
def verify_token(body: TokenIn, service: AccountService = Depends(account_service)):
    status = service.token_status(body.token)
    message = None if status == "valido" else ResetError(status).args[0]
    return TokenStatusOut(status=status.value, detail=message)


@router.post("/password-reset/confirm", response_model=MessageOut)
def confirm_reset(body: ResetConfirmIn, service: AccountService = Depends(account_service)):
    try:
        service.confirm_reset(body.token, body.password)
    except ResetError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except ValidationFailedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return MessageOut(detail="Tu contraseña se actualizó. Ya puedes iniciar sesión.")
