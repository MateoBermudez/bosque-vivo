from fastapi import APIRouter

from bosquevivo import __version__

router = APIRouter(tags=["salud"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
