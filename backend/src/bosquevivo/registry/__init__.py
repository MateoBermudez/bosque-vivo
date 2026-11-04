from importlib import import_module
from typing import TYPE_CHECKING

from bosquevivo.registry.geometry import GeometryReport, area_hectares, normalize_geometry
from bosquevivo.registry.repository import ProjectRepository

if TYPE_CHECKING:
    from bosquevivo.registry.importer import ImportSummary, import_file
    from bosquevivo.registry.karnik import KarnikSummary, import_karnik

_LAZY = {
    "ImportSummary": "bosquevivo.registry.importer",
    "import_file": "bosquevivo.registry.importer",
    "KarnikSummary": "bosquevivo.registry.karnik",
    "import_karnik": "bosquevivo.registry.karnik",
}

__all__ = [
    "GeometryReport",
    "ImportSummary",
    "KarnikSummary",
    "ProjectRepository",
    "area_hectares",
    "import_file",
    "import_karnik",
    "normalize_geometry",
]


def __getattr__(name: str):
    if name in _LAZY:
        return getattr(import_module(_LAZY[name]), name)
    raise AttributeError(name)
