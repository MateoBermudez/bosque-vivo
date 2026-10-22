"""Proveedor de datos abiertos: Hansen Global Forest Change, sin cuenta de Earth Engine.

Lee por **ventanas HTTP** los mapas de cobertura arbórea del año 2000 y de pérdida de bosque por
año (2001-2024) que Hansen et al. publican en un bucket público de Google Cloud Storage. Solo se
descarga la parte que cubre el polígono del proyecto.

Entrega datos reales para el componente de *permanencia forestal* del índice. **No calcula NDVI**:
las series de verdor (tendencia y estabilidad) siguen necesitando Earth Engine.

Hansen, M. C., et al. (2013). High-resolution global maps of 21st-century forest cover change.
Science, 342, 850-853. Versión: GFC-2024-v1.12.
"""

import hashlib
import json
import math
from datetime import date

import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, mapping, shape
from shapely.geometry.base import BaseGeometry

from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.core.logging import get_logger
from bosquevivo.satellite.models import (
    ForestBaseline,
    ForestLossPoint,
    Sensor,
    ThumbnailKind,
    TimeSeriesPoint,
)

log = get_logger(__name__)

VERSION = "GFC-2024-v1.12"
URL_TEMPLATE = (
    "https://storage.googleapis.com/earthenginepartners-hansen/"
    "GFC-2024-v1.12/Hansen_GFC-2024-v1.12_{layer}_{tile}.tif"
)
TREE_COVER_THRESHOLD = 30  # % de cobertura arbórea en el año 2000 para contar como bosque
FIRST_LOSS_YEAR = 2001
LAST_LOSS_CODE = 24  # 2024
TILE_DEGREES = 10


def tile_name(left: int, top: int) -> str:
    """Hansen nombra cada tile de 10° por su esquina superior izquierda: 10N_080W, 00N_070W…"""
    return f"{abs(top):02d}{'N' if top >= 0 else 'S'}_{abs(left):03d}{'E' if left >= 0 else 'W'}"


Bounds = tuple[float, float, float, float]


def tiles_for(bounds: Bounds) -> list[tuple[str, Bounds]]:
    """Tiles de 10° que tocan un rectángulo (min_x, min_y, max_x, max_y), con sus límites."""
    min_x, min_y, max_x, max_y = bounds
    tiles: list[tuple[str, Bounds]] = []
    top = math.ceil(max_y / TILE_DEGREES) * TILE_DEGREES
    while top - TILE_DEGREES < max_y and top > min_y:
        left = math.floor(min_x / TILE_DEGREES) * TILE_DEGREES
        while left < max_x:
            tiles.append(
                (tile_name(left, top), (left, top - TILE_DEGREES, left + TILE_DEGREES, top))
            )
            left += TILE_DEGREES
        top -= TILE_DEGREES
    return tiles


def pixel_area_ha(latitudes: np.ndarray, pixel_degrees: float) -> np.ndarray:
    """Área en hectáreas de un píxel de `pixel_degrees` a cada latitud (elipsoide WGS84)."""
    phi = np.radians(latitudes)
    meters_per_lat = 111132.92 - 559.82 * np.cos(2 * phi) + 1.175 * np.cos(4 * phi)
    meters_per_lon = 111412.84 * np.cos(phi) - 93.5 * np.cos(3 * phi) + 0.118 * np.cos(5 * phi)
    return (pixel_degrees * meters_per_lat) * (pixel_degrees * meters_per_lon) / 10_000.0


class HansenStats:
    """Hectáreas de bosque del año 2000 y de pérdida por año dentro de un polígono."""

    def __init__(self) -> None:
        self.baseline_ha = 0.0
        self.loss_by_year: dict[int, float] = {}

    def add(self, baseline_ha: float, loss_by_year: dict[int, float]) -> None:
        self.baseline_ha += baseline_ha
        for year, ha in loss_by_year.items():
            self.loss_by_year[year] = self.loss_by_year.get(year, 0.0) + ha


def tile_stats(loss: np.ndarray, cover: np.ndarray, transform) -> tuple[float, dict[int, float]]:
    """Calcula bosque base y pérdida por año de una ventana ya recortada al polígono."""
    rows = np.arange(loss.shape[0])
    latitudes = transform.f + (rows + 0.5) * transform.e
    area = np.repeat(pixel_area_ha(latitudes, abs(transform.a))[:, None], loss.shape[1], axis=1)
    forest = cover >= TREE_COVER_THRESHOLD
    by_year: dict[int, float] = {}
    for code in range(1, LAST_LOSS_CODE + 1):
        ha = float(area[(loss == code) & forest].sum())
        if ha > 0:
            by_year[FIRST_LOSS_YEAR + code - 1] = ha
    return float(area[forest].sum()), by_year


class HansenOpenProvider:
    name = "hansen"

    def __init__(self, url_template: str = URL_TEMPLATE) -> None:
        self._template = url_template
        self._cache: dict[str, HansenStats] = {}

    def _read_window(self, layer: str, tile: str, geometry: BaseGeometry):
        url = self._template.format(layer=layer, tile=tile)
        with rasterio.open(url) as source:
            data, transform = mask(source, [mapping(geometry)], crop=True, filled=True, nodata=0)
        return data[0], transform

    def _stats(self, geometry: dict) -> HansenStats:
        key = hashlib.sha256(json.dumps(geometry, sort_keys=True).encode()).hexdigest()
        if key in self._cache:
            return self._cache[key]
        polygon = shape(geometry)
        stats = HansenStats()
        try:
            with rasterio.Env(
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                GDAL_HTTP_MAX_RETRY="3",
                GDAL_HTTP_RETRY_DELAY="2",
            ):
                for name, bounds in tiles_for(polygon.bounds):
                    part = polygon.intersection(box(*bounds))
                    if part.is_empty:
                        continue
                    loss, transform = self._read_window("lossyear", name, part)
                    cover, _ = self._read_window("treecover2000", name, part)
                    stats.add(*tile_stats(loss, cover, transform))
        except Exception as exc:
            raise ExternalServiceError(f"no se pudo leer el mapa de Hansen: {exc}") from exc
        self._cache = {key: stats}  # solo se conserva el último polígono
        return stats

    def get_timeseries(
        self, geometry: dict, start: date, end: date, sensor: Sensor
    ) -> list[TimeSeriesPoint]:
        log.info("hansen_without_ndvi", note="este proveedor no calcula series NDVI")
        return []

    def get_forest_loss(self, geometry: dict) -> list[ForestLossPoint]:
        stats = self._stats(geometry)
        return [
            ForestLossPoint(year=year, ha_lost=round(ha, 2), source="hansen")
            for year, ha in sorted(stats.loss_by_year.items())
        ]

    def get_forest_baseline(self, geometry: dict) -> ForestBaseline:
        stats = self._stats(geometry)
        return ForestBaseline(
            tree_cover_ha=round(stats.baseline_ha, 2),
            threshold_percent=TREE_COVER_THRESHOLD,
            source="hansen",
        )

    def get_thumbnail(
        self, geometry: dict, start: date, end: date, kind: ThumbnailKind, sensor: Sensor
    ) -> bytes:
        raise ExternalServiceError("El proveedor de datos abiertos no genera miniaturas")

    def dataset_versions(self) -> dict[str, str]:
        return {"hansen": f"UMD {VERSION} (lectura directa, cobertura >= {TREE_COVER_THRESHOLD} %)"}
