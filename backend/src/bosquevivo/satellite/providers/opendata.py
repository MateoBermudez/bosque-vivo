"""Proveedor de datos abiertos: NDVI de MODIS + pérdida de bosque de Hansen, sin Earth Engine.

- **NDVI:** MOD13Q1 v061 (NASA), 250 m, un compuesto cada 16 días, leído por ventanas desde
  Microsoft Planetary Computer (catálogo STAC público). Solo se usan los píxeles de buena
  calidad (confiabilidad 0 o 1; se descartan nieve/hielo y nubes) y se promedian por mes.
- **Pérdida de bosque y bosque base:** Hansen Global Forest Change (ver `hansen.py`).

Es una alternativa con **menor resolución** (250 m frente a los 10 a 30 m de Sentinel-2 y Landsat):
sirve para tendencias de un territorio, no para parcelas pequeñas. Con Earth Engine el índice se
calcula con mejores imágenes; este proveedor permite obtenerlo sin cuenta de Google.
"""

from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import numpy as np
import planetary_computer
import rasterio
from pystac_client import Client
from rasterio.mask import mask
from rasterio.warp import transform_geom
from shapely.geometry import mapping, shape
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
from bosquevivo.satellite.providers.hansen import HansenOpenProvider

log = get_logger(__name__)

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "modis-13Q1-061"
NDVI_ASSET = "250m_16_days_NDVI"
RELIABILITY_ASSET = "250m_16_days_pixel_reliability"
NDVI_SCALE = 0.0001
NDVI_MIN_VALID = -2000  # por debajo es relleno (-3000)
GOOD_RELIABILITY = (0, 1)  # 0 buena, 1 marginal; 2 nieve/hielo y 3 nubes se descartan
COMPOSITE_MIDPOINT_DAYS = 8
WORKERS = 8


@dataclass(frozen=True)
class CompositeReading:
    """NDVI válido de un compuesto de 16 días dentro del polígono (todas las baldosas juntas)."""

    day: date
    values: np.ndarray
    total_pixels: int


Searcher = Callable[[tuple[float, float, float, float], date, date], list[Any]]
Reader = Callable[[Any, BaseGeometry], CompositeReading]


def monthly_points(
    readings: list[CompositeReading], sensor: Sensor, start: date, end: date
) -> list[TimeSeriesPoint]:
    """Agrupa los compuestos por mes. La fracción válida es el promedio de píxeles buenos."""
    first_month = date(start.year, start.month, 1)
    by_month: dict[date, list[CompositeReading]] = defaultdict(list)
    for reading in readings:
        month = date(reading.day.year, reading.day.month, 1)
        if first_month <= month < end:
            by_month[month].append(reading)
    points: list[TimeSeriesPoint] = []
    for month in sorted(by_month):
        group = by_month[month]
        pooled = np.concatenate([g.values for g in group])
        fractions = [g.values.size / g.total_pixels if g.total_pixels else 0.0 for g in group]
        has_values = pooled.size > 0
        points.append(
            TimeSeriesPoint(
                period=month,
                sensor=sensor,
                ndvi_mean=float(pooled.mean()) if has_values else None,
                ndvi_p10=float(np.percentile(pooled, 10)) if has_values else None,
                ndvi_p90=float(np.percentile(pooled, 90)) if has_values else None,
                valid_fraction=min(1.0, float(np.mean(fractions))),
                scene_count=len(group),
            )
        )
    return points


def merge_by_day(readings: list[CompositeReading]) -> list[CompositeReading]:
    """Une las baldosas de una misma fecha (un polígono puede cruzar varias)."""
    merged: dict[date, list[CompositeReading]] = defaultdict(list)
    for reading in readings:
        merged[reading.day].append(reading)
    return [
        CompositeReading(
            day=day,
            values=np.concatenate([g.values for g in group]),
            total_pixels=sum(g.total_pixels for g in group),
        )
        for day, group in sorted(merged.items())
    ]


def _item_day(item: Any) -> date:
    start = date.fromisoformat(str(item.properties["start_datetime"])[:10])
    return start + timedelta(days=COMPOSITE_MIDPOINT_DAYS)


def _tile_key(item: Any) -> tuple:
    return (
        item.properties.get("modis:horizontal-tile"),
        item.properties.get("modis:vertical-tile"),
        str(item.properties.get("start_datetime"))[:10],
    )


def read_composite(item: Any, geometry: BaseGeometry) -> CompositeReading:
    """Lee el NDVI y la confiabilidad de una baldosa recortados al polígono."""
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF",
        GDAL_HTTP_MAX_RETRY="3",
        GDAL_HTTP_RETRY_DELAY="2",
    ):
        with rasterio.open(item.assets[NDVI_ASSET].href) as source:
            region = transform_geom("EPSG:4326", source.crs, mapping(geometry))
            ndvi, _ = mask(source, [region], crop=True, filled=False, nodata=-3000)
        with rasterio.open(item.assets[RELIABILITY_ASSET].href) as source:
            reliability, _ = mask(source, [region], crop=True, filled=False, nodata=255)
    inside = ~np.ma.getmaskarray(ndvi[0])
    raw = np.ma.getdata(ndvi[0])
    good = (
        inside & (raw >= NDVI_MIN_VALID) & np.isin(np.ma.getdata(reliability[0]), GOOD_RELIABILITY)
    )
    return CompositeReading(
        day=_item_day(item),
        values=raw[good].astype("float64") * NDVI_SCALE,
        total_pixels=int(inside.sum()),
    )


def search_composites(
    bounds: tuple[float, float, float, float], start: date, end: date
) -> list[Any]:
    client = Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)
    search = client.search(
        collections=[COLLECTION],
        bbox=list(bounds),
        datetime=f"{start.isoformat()}/{end.isoformat()}",
    )
    unique: dict[tuple, Any] = {}
    for item in search.items():
        unique.setdefault(_tile_key(item), item)
    return list(unique.values())


class OpenDataProvider:
    name = "open"
    default_sensors = (Sensor.MODIS,)

    def __init__(
        self,
        *,
        hansen: HansenOpenProvider | None = None,
        searcher: Searcher = search_composites,
        reader: Reader = read_composite,
        workers: int = WORKERS,
    ) -> None:
        self._hansen = hansen or HansenOpenProvider()
        self._search = searcher
        self._read = reader
        self._workers = workers

    def get_timeseries(
        self, geometry: dict, start: date, end: date, sensor: Sensor
    ) -> list[TimeSeriesPoint]:
        if sensor != Sensor.MODIS:
            return []
        polygon = shape(geometry)
        try:
            items = self._search(polygon.bounds, start, end)
        except Exception as exc:
            raise ExternalServiceError(f"no se pudo consultar MODIS: {exc}") from exc
        if not items:
            return []

        def safe_read(item: Any) -> CompositeReading | None:
            try:
                return self._read(item, polygon)
            except Exception as exc:  # una baldosa que falla no debe perder toda la serie
                log.warning("modis_read_failed", day=str(_item_day(item)), error=str(exc))
                return None

        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            results = list(pool.map(safe_read, items))
        readings = [r for r in results if r is not None]
        if not readings:
            raise ExternalServiceError("no se pudo leer ningún compuesto de MODIS")
        return monthly_points(merge_by_day(readings), Sensor.MODIS, start, end)

    def get_forest_loss(self, geometry: dict) -> list[ForestLossPoint]:
        return self._hansen.get_forest_loss(geometry)

    def get_forest_baseline(self, geometry: dict) -> ForestBaseline:
        return self._hansen.get_forest_baseline(geometry)

    def get_thumbnail(
        self, geometry: dict, start: date, end: date, kind: ThumbnailKind, sensor: Sensor
    ) -> bytes:
        raise ExternalServiceError("El proveedor de datos abiertos no genera miniaturas")

    def dataset_versions(self) -> dict[str, str]:
        return {
            **self._hansen.dataset_versions(),
            "modis": "MOD13Q1 v061 (NASA, 250 m, 16 días) vía Microsoft Planetary Computer",
        }
