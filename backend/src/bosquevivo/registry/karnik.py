"""Importador de la base de contornos de Karnik et al. (2025).

Karnik, A., et al. (2025). An open-access database of nature-based carbon offset project
boundaries. Scientific Data, 12, 581. Datos: Zenodo 10.5281/zenodo.11459391 (CC BY 4.0).

Reglas de selección (ver docs/fuentes-de-datos/karnik.md):
- Se audita el **área de contabilidad** (la usada para emitir créditos) cuando existe; si no,
  el área del proyecto.
- Los proyectos que solo tienen un punto no se pueden auditar y se omiten.
- T0 es la fecha de inicio del periodo de acreditación (`Project Start Date`, mm/dd/yyyy).
- Los polígonos con más de `max_vertices` vértices se simplifican para Earth Engine y la web.
"""

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import geopandas as gpd
from pyproj import CRS
from shapely import wkt
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry
from sqlalchemy import delete
from sqlalchemy.orm import Session

from bosquevivo.core.errors import ValidationFailedError
from bosquevivo.core.logging import get_logger
from bosquevivo.db.models import ProjectDeclaration
from bosquevivo.registry.geometry import (
    MAX_ANALYSIS_VERTICES,
    WGS84,
    normalize_geometry,
    simplify_for_analysis,
)
from bosquevivo.registry.repository import ProjectRepository

log = get_logger(__name__)

SOURCE = "karnik"
VERSION = "v1 (Zenodo 10.5281/zenodo.11459391)"
DOCUMENT = "Karnik et al. (2025), Sci. Data 12:581 · Zenodo 10.5281/zenodo.11459391"
CAPTURED_BY = "import:karnik"

REQUIRED_COLUMNS = (
    "Project Name",
    "ProjectID",
    "Registry Name",
    "Project Type",
    "Country",
    "Project Start Date",
    "Geometry Type",
)

PROJECT_TYPES = {
    "AD": "Deforestación evitada (AD)",
    "ARR": "Reforestación (ARR)",
    "IFM": "Manejo forestal mejorado (IFM)",
}


@dataclass
class KarnikSummary:
    created: int = 0
    updated: int = 0
    repaired: int = 0
    simplified: int = 0
    accounting_area_used: int = 0
    skipped_points: list[str] = field(default_factory=list)
    skipped_other: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.updated


def parse_us_date(value: object) -> date | None:
    """Convierte mm/dd/yyyy (formato de Karnik) en fecha; None si no se puede."""
    text = _clean(value)
    if text is None:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def _clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in {"", "nan", "none", "nat"} else text


def _project_type(value: object) -> str | None:
    code = _clean(value)
    return PROJECT_TYPES.get(code.upper(), code) if code else None


def _accounting_geometry(row) -> BaseGeometry | None:
    text = _clean(row.get("Project Accounting Area"))
    if text is None:
        return None
    try:
        return wkt.loads(text)
    except Exception:  # WKT mal formado: se usa el área del proyecto
        return None


def _replace_declaration(session: Session, project_id: int, field_name: str, value: str) -> None:
    session.execute(
        delete(ProjectDeclaration).where(
            ProjectDeclaration.project_id == project_id,
            ProjectDeclaration.field == field_name,
            ProjectDeclaration.captured_by == CAPTURED_BY,
        )
    )
    session.add(
        ProjectDeclaration(
            project_id=project_id,
            field=field_name,
            value=value,
            source_document=DOCUMENT,
            captured_by=CAPTURED_BY,
            reviewed=True,
        )
    )


def _store_profile(session: Session, project_id: int, row, approach: str) -> None:
    """Datos de la ficha del proyecto que la web muestra aunque no haya auditoría."""
    end = parse_us_date(row.get("Project End Date"))
    fields = {
        "methodology": _clean(row.get("Methodology")),
        "developer": _clean(row.get("Project Developer Name")),
        "crediting_end": end.isoformat() if end else None,
        "processing_approach": approach if approach != "sin dato" else None,
    }
    for name, value in fields.items():
        if value:
            _replace_declaration(session, project_id, name, value)


def _is_point(row) -> bool:
    return (
        str(row["Geometry Type"]).strip().lower() == "point"
        or row.geometry is None
        or row.geometry.geom_type in {"Point", "MultiPoint"}
    )


def _import_row(
    session: Session,
    repository: ProjectRepository,
    row,
    *,
    registry_id: str,
    source_crs: CRS,
    summary: KarnikSummary,
    version: str,
    max_vertices: int,
) -> None:
    """Importa una fila con polígono. Lanza ValidationFailedError si la geometría no sirve."""
    accounting = _accounting_geometry(row)
    report = normalize_geometry(
        accounting if accounting is not None else row.geometry,
        WGS84 if accounting is not None else source_crs,
    )
    reduced = simplify_for_analysis(report.geometry, max_vertices)
    summary.repaired += int(report.repaired)
    summary.simplified += int(reduced.simplified)
    summary.accounting_area_used += int(accounting is not None)

    start = parse_us_date(row["Project Start Date"])
    stored_version = (
        f"{version[:50]}; simplif. {reduced.tolerance}°" if reduced.simplified else version
    )
    project, created = repository.upsert(
        {
            "source_registry": _clean(row["Registry Name"]) or "Karnik",
            "registry_id": registry_id,
            "name": _clean(row["Project Name"]) or f"Proyecto {registry_id}",
            "country": _clean(row["Country"]),
            "project_type": _project_type(row["Project Type"]),
            "start_year": start.year if start else None,
            "area_ha": round(report.area_ha, 2),
            "geometry": json.dumps(mapping(reduced.geometry)),
            "source": SOURCE,
            "source_version": stored_version[:80],
        }
    )
    session.flush()
    if start:
        _replace_declaration(session, project.id, "crediting_start", start.isoformat())
    approach = _clean(row.get("Processing Approach")) or "sin dato"
    used = "área de contabilidad" if accounting is not None else "área del proyecto"
    _replace_declaration(session, project.id, "geometry_source", f"{used} ({approach})")
    _store_profile(session, project.id, row, approach)
    summary.created += int(created)
    summary.updated += int(not created)


def import_karnik(
    session: Session,
    path: Path,
    *,
    country: str | None = None,
    limit: int | None = None,
    version: str = VERSION,
    max_vertices: int = MAX_ANALYSIS_VERTICES,
) -> KarnikSummary:
    if not path.exists():
        raise ValidationFailedError(f"no existe el archivo {path}")
    frame = gpd.read_file(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise ValidationFailedError(
            "el archivo no tiene el formato de la base de Karnik; faltan: " + ", ".join(missing)
        )
    if frame.crs is None:
        frame = frame.set_crs(WGS84)
    source_crs = CRS.from_user_input(frame.crs)
    repository = ProjectRepository(session)
    summary = KarnikSummary()

    for index, row in frame.iterrows():
        if limit is not None and summary.total >= limit:
            break
        row_country = _clean(row["Country"])
        if country and (row_country or "").lower() != country.lower():
            continue
        registry_id = _clean(row["ProjectID"]) or f"row-{index}"
        label = f"{registry_id} ({_clean(row['Project Name']) or 'sin nombre'})"
        if _is_point(row):
            summary.skipped_points.append(label)
            continue
        try:
            _import_row(
                session,
                repository,
                row,
                registry_id=registry_id,
                source_crs=source_crs,
                summary=summary,
                version=version,
                max_vertices=max_vertices,
            )
        except ValidationFailedError as exc:
            summary.skipped_other.append(f"{label}: {exc}")

    session.flush()
    log.info(
        "karnik_import_finished",
        created=summary.created,
        updated=summary.updated,
        skipped_points=len(summary.skipped_points),
    )
    return summary
