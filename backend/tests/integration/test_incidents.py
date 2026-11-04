import json
from datetime import date, timedelta

from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.core.incidents import (
    close_incident,
    duration_minutes,
    is_critical,
    list_incidents,
    record_incident,
    summarize,
    tracked,
)
from bosquevivo.db.base import utcnow
from bosquevivo.db.models import Incident, Project
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.models import TimeSeriesPoint
from bosquevivo.satellite.providers import FakeProvider

RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]


def test_record_classifies_origin(db):
    external = record_incident(db, "gemini", ExternalServiceError("cuota agotada"))
    internal = record_incident(db, "api", ValueError("fallo interno"))
    assert external.origin == "externo" and internal.origin == "interno"
    assert summarize(list_incidents(db)) == {
        "total": 2,
        "externos": 1,
        "internos": 1,
        "criticos": 0,
        "abiertos": 2,
    }


def test_duration_and_critical(db):
    began = utcnow() - timedelta(minutes=90)
    incident = record_incident(db, "whatsapp", "caída del túnel", started_at=began)
    assert duration_minutes(incident) is None
    close_incident(db, incident.id)
    minutes = duration_minutes(incident)
    assert minutes is not None and minutes >= 90
    assert is_critical(incident)


def test_tracked_records_and_reraises(db):
    try:
        with tracked(db, "auditoria"):
            raise ExternalServiceError("Earth Engine no responde")
    except ExternalServiceError:
        pass
    incident = db.query(Incident).one()
    assert incident.component == "auditoria" and incident.ended_at is not None


class EmptyProvider(FakeProvider):
    def get_timeseries(self, geometry, start, end, sensor):
        return []


class OutOfRangeProvider(FakeProvider):
    def get_timeseries(self, geometry, start, end, sensor):
        points = super().get_timeseries(geometry, start, end, sensor)
        broken = TimeSeriesPoint(period=date(2019, 1, 1), sensor=sensor, ndvi_mean=1.7)
        return [*points, broken]


def make_project(db) -> Project:
    project = Project(
        source_registry="test",
        registry_id="1",
        name="P",
        geometry=json.dumps({"type": "Polygon", "coordinates": [RING]}),
        source="test",
    )
    db.add(project)
    db.flush()
    return project


def test_missing_scenes_create_incident(db, tmp_path):
    project = make_project(db)
    service = SatelliteService(db, EmptyProvider(), tmp_path)
    stored = service.refresh_timeseries(
        project.id, date(2018, 1, 1), date(2020, 1, 1), sensors=(Sensor.SENTINEL2,)
    )
    assert stored == 0
    incident = db.query(Incident).one()
    assert incident.component == "series_satelitales" and incident.severity == "aviso"


def test_out_of_range_points_are_discarded(db, tmp_path):
    project = make_project(db)
    service = SatelliteService(db, OutOfRangeProvider(), tmp_path)
    service.refresh_timeseries(
        project.id, date(2018, 1, 1), date(2020, 1, 1), sensors=(Sensor.SENTINEL2,)
    )
    assert service.invalid_points == 1
