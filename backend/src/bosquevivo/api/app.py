from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bosquevivo import __version__
from bosquevivo.api.routers import health
from bosquevivo.core.errors import NotFoundError, ValidationFailedError
from bosquevivo.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Bosque Vivo", version=__version__)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationFailedError)
    async def validation_handler(_: Request, exc: ValidationFailedError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    app.include_router(health.router)
    return app


app = create_app()
