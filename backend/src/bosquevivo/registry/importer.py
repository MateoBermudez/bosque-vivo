import json
from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import mapping
from sqlalchemy.orm import Session

from bosquevivo.core.errors import ValidationFailedError
from bosquevivo.core.logging import get_logger
from bosquevivo.registry.geometry import WGS84, normalize_geometry
from bosquevivo.registry.repository import ProjectRepository

log = get_logger(__name__)

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "registry_id": ("project_id", "id", "registry_id", "projectid", "vcs_id", "gs_id"),
    "name": ("project_name", "name", "nombre", "title"),
    "country": ("country", "pais", "country_name"),
    "project_type": ("project_type", "type", "tipo", "category", "sector"),
    "start_year": (
        "start_year",
        "year_start",
        "crediting_start_year",
        "start_date",
        "project_start_date",
        "year",
    ),
    "source_registry": ("registry", "standard", "source_registry", "program", "registry_name"),
}


@dataclass
class ImportSummary:
    created: int = 0
    updated: int = 0
    repaired: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.updated


def resolve_columns(columns: list[str]) -> dict[str, str]:
    lowered = {c.lower().replace(" ", "_"): c for c in columns}
    resolved: dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lowered:
                resolved[target] = lowered[alias]
                break
    return resolved


def _to_year(value) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none"}:
        return None
    for chunk in (text[:4], text[-4:]):
        if chunk.isdigit() and 1900 <= int(chunk) <= 2100:
            return int(chunk)
    return None


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in {"", "nan", "none", "nat"} else text


def import_file(
    session: Session,
    path: Path,
    *,
    source: str,
    source_version: str | None = None,
    default_registry: str = "karnik",
    country: str | None = None,
    limit: int | None = None,
) -> ImportSummary:
    if not path.exists():
        raise ValidationFailedError(f"no existe el archivo {path}")
    frame = gpd.read_file(path)
    if frame.crs is None:
        frame = frame.set_crs(WGS84)
    columns = resolve_columns(list(frame.columns))
    if "name" not in columns and "registry_id" not in columns:
        raise ValidationFailedError("no se encontraron columnas de nombre o identificador")
    source_crs = CRS.from_user_input(frame.crs)
    repository = ProjectRepository(session)
    summary = ImportSummary()
    for index, row in frame.iterrows():
        if limit is not None and summary.total >= limit:
            break
        row_country = _clean(row[columns["country"]]) if "country" in columns else None
        if country and (row_country or "").lower() != country.lower():
            summary.skipped += 1
            continue
        try:
            report = normalize_geometry(row.geometry, source_crs)
        except ValidationFailedError as exc:
            summary.skipped += 1
            summary.errors.append(f"fila {index}: {exc}")
            continue
        if report.repaired:
            summary.repaired += 1
        registry_id = _clean(row[columns["registry_id"]]) if "registry_id" in columns else None
        name = _clean(row[columns["name"]]) if "name" in columns else None
        data = {
            "source_registry": (
                (_clean(row[columns["source_registry"]]) or default_registry).lower()
                if "source_registry" in columns
                else default_registry
            ),
            "registry_id": registry_id or f"row-{index}",
            "name": name or f"Proyecto {registry_id or index}",
            "country": row_country,
            "project_type": _clean(row[columns["project_type"]])
            if "project_type" in columns
            else None,
            "start_year": _to_year(row[columns["start_year"]]) if "start_year" in columns else None,
            "area_ha": round(report.area_ha, 2),
            "geometry": json.dumps(mapping(report.geometry)),
            "source": source,
            "source_version": source_version,
        }
        _, created = repository.upsert(data)
        if created:
            summary.created += 1
        else:
            summary.updated += 1
    session.flush()
    log.info("import_finished", created=summary.created, updated=summary.updated)
    return summary
