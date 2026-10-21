from datetime import date

import numpy as np

from bosquevivo.satellite import Sensor, monthly_composite, ndvi


def test_ndvi_basic_values():
    nir = np.array([0.5, 0.4, 0.0])
    red = np.array([0.1, 0.4, 0.0])
    result = ndvi(nir, red)
    assert round(result[0], 4) == round(0.4 / 0.6, 4)
    assert result[1] == 0
    assert np.isnan(result[2])


def test_ndvi_is_bounded():
    result = ndvi(np.array([10.0]), np.array([-9.9]))
    assert -1.0 <= result[0] <= 1.0


def test_monthly_composite_groups_scenes_and_uses_median():
    mask = np.ones(4, dtype=bool)
    scenes = [
        (date(2024, 1, 3), np.array([0.7, 0.7, 0.7, 0.7]), mask),
        (date(2024, 1, 18), np.array([0.9, 0.9, 0.9, 0.9]), mask),
        (date(2024, 2, 2), np.array([0.5, 0.5, 0.5, 0.5]), mask),
    ]
    points = monthly_composite(scenes, Sensor.SENTINEL2)
    assert [p.period for p in points] == [date(2024, 1, 1), date(2024, 2, 1)]
    assert points[0].scene_count == 2
    assert round(points[0].ndvi_mean or 0, 2) == 0.8


def test_fully_masked_scene_counts_as_no_data():
    values = np.array([0.7, 0.7])
    scenes = [(date(2024, 3, 1), values, np.zeros(2, dtype=bool))]
    point = monthly_composite(scenes, Sensor.LANDSAT)[0]
    assert point.ndvi_mean is None
    assert point.valid_fraction == 0.0
    assert point.scene_count == 0
