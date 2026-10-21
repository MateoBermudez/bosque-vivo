from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class SeriesPoint:
    period: date
    ndvi_mean: float | None
    valid_fraction: float
    scene_count: int


@dataclass(frozen=True)
class AuditInputs:
    t0: date | None
    declared_area_ha: float | None
    baseline_forest_ha: float | None
    series: list[SeriesPoint] = field(default_factory=list)
    sensor: str = "s2"
    loss_by_year: dict[int, float] = field(default_factory=dict)
