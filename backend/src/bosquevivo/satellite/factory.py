from bosquevivo.core.config import Settings
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.satellite.provider import SatelliteProvider

PROCESSING_HINT = (
    "el cálculo satelital necesita las dependencias de procesamiento "
    "(uv sync --extra procesamiento); en Vercel se ejecuta desde un equipo con la CLI"
)


def build_provider(settings: Settings) -> SatelliteProvider:
    try:
        if settings.satellite_provider == "fake":
            from bosquevivo.satellite.providers.fake import FakeProvider

            return FakeProvider()
        if settings.satellite_provider == "open":
            from bosquevivo.satellite.providers.opendata import OpenDataProvider

            return OpenDataProvider()
        if settings.satellite_provider == "hansen":
            from bosquevivo.satellite.providers.hansen import HansenOpenProvider

            return HansenOpenProvider()
        from bosquevivo.satellite.providers.gee import GeeProvider
    except ModuleNotFoundError as exc:
        raise ExternalServiceError(f"{PROCESSING_HINT} (falta {exc.name})") from exc
    return GeeProvider(settings.gee_project, settings.cloud_max_percent)
