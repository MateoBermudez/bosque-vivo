from bosquevivo.core.config import Settings
from bosquevivo.satellite.provider import SatelliteProvider
from bosquevivo.satellite.providers.fake import FakeProvider
from bosquevivo.satellite.providers.gee import GeeProvider


def build_provider(settings: Settings) -> SatelliteProvider:
    if settings.satellite_provider == "fake":
        return FakeProvider()
    return GeeProvider(settings.gee_project)
