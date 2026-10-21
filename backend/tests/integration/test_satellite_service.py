import json
from datetime import date

import pytest

from bosquevivo.core.errors import NotFoundError
from bosquevivo.db.models import ForestLoss, ImageAsset, NdviObservation, Project
from bosquevivo.satellite import SatelliteService, Sensor, ThumbnailKind
from bosquevivo.satellite.providers import FakeProvider

RING = [[-75.0, 5.0], [-74.99, 5.0], [-74.99, 5.01], [-75.0, 5.01], [-75.0, 5.0]]


@pytest.fixture
def project(db):
    item = Project(
        source_registry="test",
        registry_id="1",
        name="Demo",
        geometry=json.dumps({"type": "Polygon", "coordinates": [RING]}),
        source="test",
    )
    db.add(item)
    db.commit()
    return item


def test_refresh_timeseries_stores_months(db, project, tmp_path):
    service = SatelliteService(db, FakeProvider(), tmp_path)
    stored = service.refresh_timeseries(
        project.id, date(2020, 1, 1), date(2020, 12, 31), sensors=(Sensor.SENTINEL2,)
    )
    assert stored == 12
    assert db.query(NdviObservation).count() == 12


def test_refresh_replaces_previous_observations(db, project, tmp_path):
    service = SatelliteService(db, FakeProvider(), tmp_path)
    args = (project.id, date(2020, 1, 1), date(2020, 6, 30))
    service.refresh_timeseries(*args, sensors=(Sensor.LANDSAT,))
    service.refresh_timeseries(*args, sensors=(Sensor.LANDSAT,))
    assert db.query(NdviObservation).count() == 6


def test_sentinel2_not_requested_before_launch_window(db, project, tmp_path):
    service = SatelliteService(db, FakeProvider(), tmp_path)
    stored = service.refresh_timeseries(
        project.id, date(2010, 1, 1), date(2012, 1, 1), sensors=(Sensor.SENTINEL2,)
    )
    assert stored == 0


def test_forest_loss_is_stored(db, project, tmp_path):
    service = SatelliteService(db, FakeProvider(loss_by_year={2021: 3.5, 2022: 1.2}), tmp_path)
    assert service.refresh_forest_loss(project.id) == 2
    assert db.query(ForestLoss).count() == 2


def test_thumbnail_is_cached(db, project, tmp_path):
    service = SatelliteService(db, FakeProvider(), tmp_path)
    first = service.thumbnail(project.id, date(2020, 1, 1), date(2020, 2, 1), ThumbnailKind.NDVI)
    second = service.thumbnail(project.id, date(2020, 1, 1), date(2020, 2, 1), ThumbnailKind.NDVI)
    assert first.id == second.id
    assert db.query(ImageAsset).count() == 1


def test_unknown_project_raises(db, tmp_path):
    service = SatelliteService(db, FakeProvider(), tmp_path)
    with pytest.raises(NotFoundError):
        service.refresh_forest_loss(999)
