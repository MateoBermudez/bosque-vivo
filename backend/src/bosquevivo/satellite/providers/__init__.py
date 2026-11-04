from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bosquevivo.satellite.providers.fake import FakeProvider
    from bosquevivo.satellite.providers.gee import GeeProvider
    from bosquevivo.satellite.providers.hansen import HansenOpenProvider
    from bosquevivo.satellite.providers.opendata import OpenDataProvider

_PROVIDERS = {
    "FakeProvider": "bosquevivo.satellite.providers.fake",
    "GeeProvider": "bosquevivo.satellite.providers.gee",
    "HansenOpenProvider": "bosquevivo.satellite.providers.hansen",
    "OpenDataProvider": "bosquevivo.satellite.providers.opendata",
}

__all__ = ["FakeProvider", "GeeProvider", "HansenOpenProvider", "OpenDataProvider"]


def __getattr__(name: str):
    if name in _PROVIDERS:
        return getattr(import_module(_PROVIDERS[name]), name)
    raise AttributeError(name)
