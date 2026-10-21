import json

import pytest

from bosquevivo.core.errors import ValidationFailedError
from bosquevivo.db.models import Project
from bosquevivo.registry import ProjectRepository, import_file


def write_geojson(path, features):
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))


def feature(project_id, name, country, *, lon=-75.0, lat=5.0, size=0.02):
    ring = [[lon, lat], [lon + size, lat], [lon + size, lat + size], [lon, lat + size], [lon, lat]]
    return {
        "type": "Feature",
        "properties": {
            "project_id": project_id,
            "project_name": name,
            "country": country,
            "start_date": "2015-06-01",
        },
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "projects.geojson"
    write_geojson(
        path,
        [
            feature("A1", "Bosque Norte", "Colombia"),
            feature("B2", "Selva Sur", "Peru", lon=-70.0, lat=-5.0),
        ],
    )
    return path


def test_import_creates_projects(db, sample):
    summary = import_file(db, sample, source="test", source_version="v1")
    assert summary.created == 2
    project = ProjectRepository(db).find_by_registry("karnik", "A1")
    assert project is not None
    assert project.start_year == 2015
    assert project.area_ha and project.area_ha > 0


def test_import_is_idempotent(db, sample):
    import_file(db, sample, source="test")
    summary = import_file(db, sample, source="test")
    assert summary.created == 0
    assert summary.updated == 2
    assert db.query(Project).count() == 2


def test_import_filters_by_country(db, sample):
    summary = import_file(db, sample, source="test", country="Colombia")
    assert summary.created == 1
    assert summary.skipped == 1


def test_locate_point_inside_polygon(db, sample):
    import_file(db, sample, source="test")
    repo = ProjectRepository(db)
    found = repo.locate(5.01, -74.99)
    assert found is not None and found.registry_id == "A1"
    assert repo.locate(40.0, 10.0) is None


def test_missing_file_raises(db, tmp_path):
    with pytest.raises(ValidationFailedError):
        import_file(db, tmp_path / "nope.geojson", source="x")
