from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date

import numpy as np

from bosquevivo.satellite.models import Sensor, TimeSeriesPoint


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    nir = nir.astype(np.float64)
    red = red.astype(np.float64)
    denominator = nir + red
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(denominator == 0, np.nan, (nir - red) / denominator)
    return np.clip(result, -1.0, 1.0)


def scene_stats(values: np.ndarray, valid_mask: np.ndarray) -> dict[str, float | None]:
    total = values.size
    usable = values[valid_mask & ~np.isnan(values)]
    if total == 0 or usable.size == 0:
        return {"mean": None, "p10": None, "p90": None, "valid_fraction": 0.0}
    return {
        "mean": float(np.mean(usable)),
        "p10": float(np.percentile(usable, 10)),
        "p90": float(np.percentile(usable, 90)),
        "valid_fraction": float(usable.size / total),
    }


def month_start(day: date) -> date:
    return day.replace(day=1)


def monthly_composite(
    scenes: Iterable[tuple[date, np.ndarray, np.ndarray]], sensor: Sensor
) -> list[TimeSeriesPoint]:
    grouped: dict[date, list[dict[str, float | None]]] = defaultdict(list)
    for day, values, valid_mask in scenes:
        grouped[month_start(day)].append(scene_stats(values, valid_mask))
    points: list[TimeSeriesPoint] = []
    for period in sorted(grouped):
        points.append(_aggregate(period, grouped[period], sensor))
    return points


def _median(values: Sequence[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return float(np.median(clean)) if clean else None


def _aggregate(
    period: date, stats: list[dict[str, float | None]], sensor: Sensor
) -> TimeSeriesPoint:
    usable = [s for s in stats if s["mean"] is not None]
    return TimeSeriesPoint(
        period=period,
        sensor=sensor,
        ndvi_mean=_median([s["mean"] for s in usable]),
        ndvi_p10=_median([s["p10"] for s in usable]),
        ndvi_p90=_median([s["p90"] for s in usable]),
        valid_fraction=float(np.mean([s["valid_fraction"] or 0.0 for s in stats])),
        scene_count=len(usable),
    )
