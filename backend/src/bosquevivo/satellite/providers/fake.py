import hashlib
import io
from datetime import date

import numpy as np
from matplotlib import pyplot as plt
from shapely.geometry import shape

from bosquevivo.registry.geometry import area_hectares
from bosquevivo.satellite.models import (
    ForestBaseline,
    ForestLossPoint,
    Sensor,
    ThumbnailKind,
    TimeSeriesPoint,
)


class FakeProvider:
    name = "fake"

    def __init__(
        self,
        *,
        base_ndvi: float = 0.8,
        drop_year: int | None = None,
        drop_size: float = 0.3,
        loss_by_year: dict[int, float] | None = None,
        valid_fraction: float = 0.9,
    ) -> None:
        self.base_ndvi = base_ndvi
        self.drop_year = drop_year
        self.drop_size = drop_size
        self.loss_by_year = loss_by_year or {}
        self.valid_fraction = valid_fraction

    def _seed(self, geometry: dict) -> int:
        digest = hashlib.sha256(repr(sorted(geometry.items())).encode()).hexdigest()
        return int(digest[:8], 16)

    def get_timeseries(
        self, geometry: dict, start: date, end: date, sensor: Sensor
    ) -> list[TimeSeriesPoint]:
        rng = np.random.default_rng(self._seed(geometry))
        points: list[TimeSeriesPoint] = []
        year, month = start.year, start.month
        while date(year, month, 1) <= end:
            level = self.base_ndvi + float(rng.normal(0, 0.01))
            if self.drop_year is not None and year >= self.drop_year:
                level -= self.drop_size
            points.append(
                TimeSeriesPoint(
                    period=date(year, month, 1),
                    sensor=sensor,
                    ndvi_mean=round(level, 4),
                    ndvi_p10=round(level - 0.08, 4),
                    ndvi_p90=round(level + 0.06, 4),
                    valid_fraction=self.valid_fraction,
                    scene_count=4,
                )
            )
            month += 1
            if month > 12:
                year, month = year + 1, 1
        return points

    def get_forest_loss(self, geometry: dict) -> list[ForestLossPoint]:
        return [
            ForestLossPoint(year=year, ha_lost=ha, source="fake")
            for year, ha in sorted(self.loss_by_year.items())
        ]

    def get_forest_baseline(self, geometry: dict) -> ForestBaseline:
        return ForestBaseline(tree_cover_ha=area_hectares(shape(geometry)) * 0.95, source="fake")

    def get_thumbnail(
        self, geometry: dict, start: date, end: date, kind: ThumbnailKind, sensor: Sensor
    ) -> bytes:
        rng = np.random.default_rng(self._seed(geometry) + start.toordinal())
        data = rng.random((64, 64))
        figure, axis = plt.subplots(figsize=(2, 2), dpi=64)
        axis.imshow(data, cmap="Greens" if kind != ThumbnailKind.NATURAL else "gray")
        axis.axis("off")
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", bbox_inches="tight")
        plt.close(figure)
        return buffer.getvalue()

    def dataset_versions(self) -> dict[str, str]:
        return {"provider": "fake"}
