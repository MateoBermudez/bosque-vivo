from dataclasses import dataclass

import numpy as np
import shapely
from pyproj import CRS, Transformer
from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.geometry.base import BaseGeometry

from bosquevivo.core.errors import ValidationFailedError

WGS84 = CRS.from_epsg(4326)
EQUAL_AREA = CRS.from_epsg(6933)


@dataclass(frozen=True)
class GeometryReport:
    geometry: MultiPolygon | Polygon
    repaired: bool
    area_ha: float


def _polygons_only(geom: BaseGeometry) -> MultiPolygon | Polygon:
    if isinstance(geom, Polygon | MultiPolygon):
        return geom
    parts = [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon | MultiPolygon)]
    flat: list[Polygon] = []
    for part in parts:
        if isinstance(part, MultiPolygon):
            flat.extend(part.geoms)
        else:
            flat.append(part)
    if not flat:
        raise ValidationFailedError("la geometría no contiene polígonos")
    return flat[0] if len(flat) == 1 else MultiPolygon(flat)


def reproject(geom: BaseGeometry, source: CRS, target: CRS) -> BaseGeometry:
    if source == target:
        return geom
    transformer = Transformer.from_crs(source, target, always_xy=True)

    def convert(coords: np.ndarray) -> np.ndarray:
        x, y = transformer.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])

    return shapely.transform(geom, convert)


def area_hectares(geom: BaseGeometry) -> float:
    projected = reproject(geom, WGS84, EQUAL_AREA)
    return float(projected.area) / 10_000.0


def normalize_geometry(geom: BaseGeometry | dict, source_crs: CRS = WGS84) -> GeometryReport:
    parsed = shape(geom) if isinstance(geom, dict) else geom
    if parsed is None or parsed.is_empty:
        raise ValidationFailedError("geometría vacía")
    repaired = False
    if not parsed.is_valid:
        parsed = make_valid(parsed)
        repaired = True
    polygons = _polygons_only(parsed)
    polygons = reproject(polygons, source_crs, WGS84)
    if not polygons.is_valid:
        polygons = _polygons_only(make_valid(polygons))
        repaired = True
    bounds = polygons.bounds
    if not (-180 <= bounds[0] <= 180 and -90 <= bounds[1] <= 90):
        raise ValidationFailedError("coordenadas fuera de rango WGS84")
    area = area_hectares(polygons)
    if area <= 0:
        raise ValidationFailedError("el polígono tiene área cero")
    return GeometryReport(geometry=_polygons_only(polygons), repaired=repaired, area_ha=area)


# Tolerancias en grados (0,0001° ≈ 11 m, similar a un píxel de Sentinel-2).
SIMPLIFY_TOLERANCES = (0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005)
MAX_ANALYSIS_VERTICES = 20_000


@dataclass(frozen=True)
class SimplifiedGeometry:
    geometry: MultiPolygon | Polygon
    tolerance: float
    original_vertices: int
    vertices: int
    area_change_pct: float

    @property
    def simplified(self) -> bool:
        return self.tolerance > 0


def vertex_count(geom: BaseGeometry) -> int:
    return int(shapely.get_num_coordinates(geom))


def keep_largest_parts(geom: MultiPolygon | Polygon, max_parts: int) -> MultiPolygon | Polygon:
    """Deja solo las `max_parts` partes de mayor área. Sirve para dibujar proyectos formados por
    miles de parcelas diminutas, que la simplificación de vértices no logra aligerar."""
    if not isinstance(geom, MultiPolygon) or len(geom.geoms) <= max_parts:
        return geom
    largest = sorted(geom.geoms, key=lambda part: part.area, reverse=True)[:max_parts]
    return MultiPolygon(largest)


def simplify_geometry(
    geom: BaseGeometry, tolerance: float, max_parts: int | None = None
) -> MultiPolygon | Polygon:
    """Simplifica conservando la topología; si algo queda inválido lo repara.
    Con `max_parts` conserva solo las partes más grandes (vista de mapa)."""
    polygons = _polygons_only(geom)
    if max_parts is not None:
        polygons = keep_largest_parts(polygons, max_parts)
    simplified = polygons.simplify(tolerance, preserve_topology=True)
    if simplified.is_empty:
        return polygons
    if not simplified.is_valid:
        simplified = make_valid(simplified)
    return _polygons_only(simplified)


def simplify_for_analysis(
    geom: MultiPolygon | Polygon, max_vertices: int = MAX_ANALYSIS_VERTICES
) -> SimplifiedGeometry:
    """Reduce polígonos con demasiados vértices (p. ej. 1 millón) para que quepan en una petición
    a Earth Engine y en la base. Usa la menor tolerancia que baje de `max_vertices`."""
    original = vertex_count(geom)
    if original <= max_vertices:
        return SimplifiedGeometry(geom, 0.0, original, original, 0.0)
    base_area = area_hectares(geom)
    result = geom
    used = SIMPLIFY_TOLERANCES[-1]
    for tolerance in SIMPLIFY_TOLERANCES:
        result = simplify_geometry(geom, tolerance)
        used = tolerance
        if vertex_count(result) <= max_vertices:
            break
    change = abs(area_hectares(result) - base_area) / base_area * 100.0 if base_area else 0.0
    return SimplifiedGeometry(result, used, original, vertex_count(result), round(change, 3))
