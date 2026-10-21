import json
from datetime import date

import ee
import httpx

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

SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
CLOUD_SCORE_COLLECTION = "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"
LANDSAT_COLLECTIONS = (
    "LANDSAT/LT05/C02/T1_L2",
    "LANDSAT/LE07/C02/T1_L2",
    "LANDSAT/LC08/C02/T1_L2",
    "LANDSAT/LC09/C02/T1_L2",
)
HANSEN_DATASET = "UMD/hansen/global_forest_change_2024_v1_12"
CLOUD_SCORE_THRESHOLD = 0.6
TREE_COVER_THRESHOLD = 30
MAX_PIXELS = 1_000_000_000


def _scale_for(area_ha: float) -> int:
    if area_ha < 2_000:
        return 10
    if area_ha < 20_000:
        return 30
    return 60


def _info(value) -> dict:
    return value.getInfo() or {}


class GeeProvider:
    name = "gee"

    def __init__(self, project: str) -> None:
        if not project:
            raise ExternalServiceError("GEE_PROJECT no está configurado")
        self._ee = ee
        try:
            ee.Initialize(project=project)
        except Exception as exc:
            raise ExternalServiceError(f"no se pudo iniciar Earth Engine: {exc}") from exc

    def _region(self, geometry: dict):
        return self._ee.Geometry(json.loads(json.dumps(geometry)))

    def _area_ha(self, region) -> float:
        return float(region.area(maxError=10).getInfo()) / 10_000.0

    def _s2_collection(self, region, start: date, end: date):
        ee = self._ee
        scores = ee.ImageCollection(CLOUD_SCORE_COLLECTION)
        collection = (
            ee.ImageCollection(SENTINEL2_COLLECTION)
            .filterBounds(region)
            .filterDate(start.isoformat(), end.isoformat())
            .linkCollection(scores, ["cs_cdf"])
        )

        def prepare(image):
            valid = image.select("cs_cdf").gte(CLOUD_SCORE_THRESHOLD)
            index = image.normalizedDifference(["B8", "B4"]).rename("ndvi")
            return index.addBands(valid.rename("valid")).copyProperties(
                image, ["system:time_start"]
            )

        return collection.map(prepare)

    def _landsat_collection(self, region, start: date, end: date):
        ee = self._ee

        def prepare(image, nir: str, red: str):
            qa = image.select("QA_PIXEL")
            clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
            scaled = image.select([nir, red]).multiply(0.0000275).add(-0.2)
            index = scaled.normalizedDifference([nir, red]).rename("ndvi")
            return index.addBands(clear.rename("valid")).copyProperties(
                image, ["system:time_start"]
            )

        merged = ee.ImageCollection([])
        for name in LANDSAT_COLLECTIONS:
            bands = ("SR_B5", "SR_B4") if "LC0" in name else ("SR_B4", "SR_B3")
            part = (
                ee.ImageCollection(name)
                .filterBounds(region)
                .filterDate(start.isoformat(), end.isoformat())
                .map(lambda img, b=bands: prepare(img, b[0], b[1]))
            )
            merged = merged.merge(part)
        return merged

    def get_timeseries(
        self, geometry: dict, start: date, end: date, sensor: Sensor
    ) -> list[TimeSeriesPoint]:
        ee = self._ee
        region = self._region(geometry)
        scale = _scale_for(self._area_ha(region))
        collection = (
            self._s2_collection(region, start, end)
            if sensor == Sensor.SENTINEL2
            else self._landsat_collection(region, start, end)
        )
        reducer = (
            ee.Reducer.mean()
            .combine(ee.Reducer.percentile([10, 90]), sharedInputs=True)
            .combine(ee.Reducer.count(), sharedInputs=True)
        )
        points: list[TimeSeriesPoint] = []
        year, month = start.year, start.month
        while date(year, month, 1) < end:
            nxt = date(year + (month == 12), month % 12 + 1, 1)
            monthly = collection.filterDate(date(year, month, 1).isoformat(), nxt.isoformat())
            count = int(monthly.size().getInfo())
            if count:
                masked = monthly.map(lambda img: img.select("ndvi").updateMask(img.select("valid")))
                composite = masked.median()
                stats = _info(
                    composite.reduceRegion(
                        reducer, region, scale, maxPixels=MAX_PIXELS, bestEffort=True
                    )
                )
                total = (
                    monthly.first()
                    .select("ndvi")
                    .reduceRegion(
                        ee.Reducer.count(), region, scale, maxPixels=MAX_PIXELS, bestEffort=True
                    )
                    .getInfo()
                    .get("ndvi")
                    or 0
                )
                valid = stats.get("ndvi_count") or 0
                points.append(
                    TimeSeriesPoint(
                        period=date(year, month, 1),
                        sensor=sensor,
                        ndvi_mean=stats.get("ndvi_mean"),
                        ndvi_p10=stats.get("ndvi_p10"),
                        ndvi_p90=stats.get("ndvi_p90"),
                        valid_fraction=min(1.0, valid / total) if total else 0.0,
                        scene_count=count,
                    )
                )
            year, month = nxt.year, nxt.month
        return points

    def get_forest_loss(self, geometry: dict) -> list[ForestLossPoint]:
        ee = self._ee
        region = self._region(geometry)
        hansen = ee.Image(HANSEN_DATASET)
        forest = hansen.select("treecover2000").gte(TREE_COVER_THRESHOLD)
        loss_year = hansen.select("lossyear").updateMask(forest)
        area = ee.Image.pixelArea().divide(10_000)
        grouped = _info(
            area.addBands(loss_year).reduceRegion(
                ee.Reducer.sum().group(groupField=1, groupName="year"),
                region,
                30,
                maxPixels=MAX_PIXELS,
                bestEffort=True,
            )
        )
        result: list[ForestLossPoint] = []
        for group in grouped.get("groups", []):
            code = int(group["year"])
            if code > 0:
                result.append(ForestLossPoint(year=2000 + code, ha_lost=float(group["sum"])))
        return sorted(result, key=lambda p: p.year)

    def get_forest_baseline(self, geometry: dict) -> ForestBaseline:
        ee = self._ee
        region = self._region(geometry)
        forest = ee.Image(HANSEN_DATASET).select("treecover2000").gte(TREE_COVER_THRESHOLD)
        total = _info(
            ee.Image.pixelArea()
            .divide(10_000)
            .updateMask(forest)
            .reduceRegion(ee.Reducer.sum(), region, 30, maxPixels=MAX_PIXELS, bestEffort=True)
        ).get("area", 0.0)
        return ForestBaseline(
            tree_cover_ha=float(total or 0.0), threshold_percent=TREE_COVER_THRESHOLD
        )

    def get_thumbnail(
        self, geometry: dict, start: date, end: date, kind: ThumbnailKind, sensor: Sensor
    ) -> bytes:
        ee = self._ee
        region = self._region(geometry)
        s2 = (
            ee.ImageCollection(SENTINEL2_COLLECTION)
            .filterBounds(region)
            .filterDate(start.isoformat(), end.isoformat())
            .linkCollection(ee.ImageCollection(CLOUD_SCORE_COLLECTION), ["cs_cdf"])
            .map(lambda img: img.updateMask(img.select("cs_cdf").gte(CLOUD_SCORE_THRESHOLD)))
            .median()
        )
        if kind == ThumbnailKind.NATURAL:
            image = s2.visualize(bands=["B4", "B3", "B2"], min=0, max=3000)
        elif kind == ThumbnailKind.FALSE_COLOR:
            image = s2.visualize(bands=["B8", "B4", "B3"], min=0, max=4000)
        else:
            image = s2.normalizedDifference(["B8", "B4"]).visualize(
                min=0, max=1, palette=["#8c510a", "#f6e8c3", "#a6d96a", "#1a9641", "#00441b"]
            )
        url = image.getThumbURL({"region": region, "dimensions": 512, "format": "png"})
        response = httpx.get(url, timeout=120)
        if response.status_code != 200:
            raise ExternalServiceError(f"error al obtener la miniatura: {response.status_code}")
        return response.content

    def dataset_versions(self) -> dict[str, str]:
        return {
            "sentinel2": SENTINEL2_COLLECTION,
            "cloud_score": CLOUD_SCORE_COLLECTION,
            "landsat": ",".join(LANDSAT_COLLECTIONS),
            "hansen": HANSEN_DATASET,
        }
