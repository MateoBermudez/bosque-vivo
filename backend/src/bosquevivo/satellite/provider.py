from datetime import date
from typing import Protocol

from bosquevivo.satellite.models import (
    ForestBaseline,
    ForestLossPoint,
    Sensor,
    ThumbnailKind,
    TimeSeriesPoint,
)


class SatelliteProvider(Protocol):
    name: str

    def get_timeseries(
        self, geometry: dict, start: date, end: date, sensor: Sensor
    ) -> list[TimeSeriesPoint]: ...

    def get_forest_loss(self, geometry: dict) -> list[ForestLossPoint]: ...

    def get_forest_baseline(self, geometry: dict) -> ForestBaseline: ...

    def get_thumbnail(
        self, geometry: dict, start: date, end: date, kind: ThumbnailKind, sensor: Sensor
    ) -> bytes: ...

    def dataset_versions(self) -> dict[str, str]: ...
