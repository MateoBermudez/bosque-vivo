import json
from datetime import date
from pathlib import Path

import pytest

from bosquevivo.db.models import Job, Project
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.providers import FakeProvider

RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]
ADMIN = {"X-Admin-Token": "secreto"}


@pytest.fixture
def project(db):
    item = Project(
        source_registry="test",
        registry_id="1",
        name="Reserva",
        country="Colombia",
        geometry=json.dumps({"type": "Polygon", "coordinates": [RING]}),
        source="test",
    )
    db.add(item)
    db.commit()
    return item


def test_list_and_get_projects(client, project):
    listed = client.get("/api/v1/projects").json()
    assert [p["name"] for p in listed] == ["Reserva"]
    assert client.get(f"/api/v1/projects/{project.id}").json()["country"] == "Colombia"
    assert client.get("/api/v1/projects/999").status_code == 404


def test_locate_point(client, project):
    found = client.get("/api/v1/projects/locate", params={"lat": 5.05, "lon": -74.95})
    assert found.status_code == 200
    assert client.get("/api/v1/projects/locate", params={"lat": 40, "lon": 10}).status_code == 404


def test_request_audit_requires_admin_token(client, project):
    assert client.post(f"/api/v1/projects/{project.id}/audit").status_code == 401
    wrong = client.post(f"/api/v1/projects/{project.id}/audit", headers={"X-Admin-Token": "x"})
    assert wrong.status_code == 401


def test_request_audit_enqueues_job(client, db, project):
    response = client.post(f"/api/v1/projects/{project.id}/audit", headers=ADMIN)
    assert response.status_code == 200
    assert db.query(Job).one().kind == "calculate_audit"
    assert client.get(f"/api/v1/jobs/{response.json()['id']}").json()["status"] == "queued"


def test_audit_without_runs_is_404(client, project):
    assert client.get(f"/api/v1/projects/{project.id}/audit").status_code == 404


def test_report_format_validation(client):
    assert client.post("/api/v1/audits/1/report?format=exe", headers=ADMIN).status_code == 422


def test_admin_import(client, db, tmp_path: Path):
    feature = {
        "type": "Feature",
        "properties": {"project_id": "Z1", "project_name": "Importado", "country": "Peru"},
        "geometry": {"type": "Polygon", "coordinates": [RING]},
    }
    path = tmp_path / "p.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection", "features": [feature]}))
    response = client.post(
        "/api/v1/admin/import", headers=ADMIN, json={"path": str(path), "source": "test"}
    )
    assert response.status_code == 200
    assert response.json()["created"] == 1
    assert client.post("/api/v1/admin/import", json={"path": "x", "source": "y"}).status_code == 401


def test_geometry_and_series_endpoints(client, db, project):
    sat = SatelliteService(db, FakeProvider(loss_by_year={2021: 2.0}), Path("."))
    sat.refresh_timeseries(
        project.id, date(2020, 1, 1), date(2020, 6, 30), sensors=(Sensor.SENTINEL2,)
    )
    sat.refresh_forest_loss(project.id)
    db.commit()
    geometry = client.get(f"/api/v1/projects/{project.id}/geometry").json()
    assert geometry["geometry"]["type"] == "Polygon"
    series = client.get(f"/api/v1/projects/{project.id}/series").json()
    assert len(series["ndvi"]) == 6
    assert series["loss"] == [{"year": 2021, "ha_lost": 2.0}]
    assert client.get("/api/v1/projects/999/series").status_code == 404
