import pytest
from shapely.geometry import Polygon

from bosquevivo.core.errors import ValidationFailedError
from bosquevivo.registry import area_hectares, normalize_geometry


def square(lon: float, lat: float, size: float = 0.01) -> Polygon:
    return Polygon([(lon, lat), (lon + size, lat), (lon + size, lat + size), (lon, lat + size)])


def test_area_of_small_square_near_equator():
    area = area_hectares(square(-75.0, 5.0, 0.01))
    assert 115 < area < 130


def test_bowtie_polygon_is_repaired():
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
    report = normalize_geometry(bowtie)
    assert report.repaired
    assert report.geometry.is_valid


def test_empty_geometry_is_rejected():
    with pytest.raises(ValidationFailedError):
        normalize_geometry(Polygon())


def test_geojson_dict_is_accepted():
    geojson = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [0, 0.01], [0.01, 0.01], [0.01, 0], [0, 0]]],
    }
    assert normalize_geometry(geojson).area_ha > 0
