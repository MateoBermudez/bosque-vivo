from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from bosquevivo.db.models import NdviObservation, Project


def make_project(**overrides):
    data = {
        "source_registry": "verra",
        "registry_id": "1001",
        "name": "Proyecto Demo",
        "geometry": '{"type":"Polygon","coordinates":[[[0,0],[0,1],[1,1],[1,0],[0,0]]]}',
        "source": "test",
    }
    data.update(overrides)
    return Project(**data)


def test_project_roundtrip(db):
    db.add(make_project())
    db.commit()
    assert db.query(Project).one().name == "Proyecto Demo"


def test_project_registry_pair_is_unique(db):
    db.add(make_project())
    db.commit()
    db.add(make_project())
    with pytest.raises(IntegrityError):
        db.commit()


def test_ndvi_observation_unique_per_period_and_sensor(db):
    project = make_project()
    db.add(project)
    db.flush()
    db.add(NdviObservation(project_id=project.id, period=date(2024, 1, 1), sensor="s2"))
    db.commit()
    db.add(NdviObservation(project_id=project.id, period=date(2024, 1, 1), sensor="s2"))
    with pytest.raises(IntegrityError):
        db.commit()
