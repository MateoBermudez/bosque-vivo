import hmac
from collections.abc import Iterator
from functools import lru_cache

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from bosquevivo.ai.llm import LLMProvider
from bosquevivo.assistant.runtime import build_llm
from bosquevivo.core.config import Settings, get_settings
from bosquevivo.db.session import get_session
from bosquevivo.satellite.factory import build_provider
from bosquevivo.satellite.provider import SatelliteProvider


def db_session() -> Iterator[Session]:
    with get_session() as session:
        yield session


def require_admin(
    x_admin_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.admin_token
    if not expected or not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="token de administración inválido")


@lru_cache
def get_llm() -> LLMProvider:
    return build_llm(get_settings())


@lru_cache
def get_satellite_provider() -> SatelliteProvider | None:
    try:
        return build_provider(get_settings())
    except Exception:
        return None
