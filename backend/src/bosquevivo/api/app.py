from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bosquevivo import __version__
from bosquevivo.api.routers import admin, audits, health, projects
from bosquevivo.core.config import get_settings
from bosquevivo.core.errors import NotFoundError, ValidationFailedError
from bosquevivo.core.logging import configure_logging, get_logger
from bosquevivo.db.session import get_engine, init_db, make_session_factory
from bosquevivo.jobs import JobWorker
from bosquevivo.jobs.tasks import (
    CALCULATE_AUDIT,
    GENERATE_REPORT,
    generate_report,
    make_calculate_audit,
)
from bosquevivo.satellite.factory import build_provider

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_db()
    worker = JobWorker(make_session_factory(get_engine()))
    worker.register(GENERATE_REPORT, generate_report)
    try:
        worker.register(CALCULATE_AUDIT, make_calculate_audit(build_provider(settings)))
    except Exception as exc:
        log.warning("satellite_provider_unavailable", error=str(exc))
    worker.start()
    app.state.worker = worker
    try:
        yield
    finally:
        worker.stop()


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Bosque Vivo", version=__version__, lifespan=lifespan)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationFailedError)
    async def validation_handler(_: Request, exc: ValidationFailedError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(audits.router)
    app.include_router(admin.router)
    return app


app = create_app()
