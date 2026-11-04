import json
from pathlib import Path

import pytest

from bosquevivo.core.errors import ValidationFailedError
from bosquevivo.db.models import Project
from bosquevivo.registry.importer import import_file

RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]
BOWTIE = [[-75.0, 5.0], [-74.9, 5.1], [-74.9, 5.0], [-75.0, 5.1], [-75.0, 5.0]]

KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<Placemark><name>Reserva KML</name>
<ExtendedData>
  <Data name="project_id"><value>VCS-900</value></Data>
  <Data name="start_year"><value>2016</value></Data>
</ExtendedData>
<Polygon><outerBoundaryIs><LinearRing><coordinates>
-75.0,5.0 -74.9,5.0 -74.9,5.1 -75.0,5.1 -75.0,5.0
</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>
</Document></kml>
"""


def write_geojson(path: Path, features: list[dict]) -> Path:
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return path


def feature(ring, **properties) -> dict:
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def test_kml_import(db, tmp_path):
    path = tmp_path / "proyectos.kml"
    path.write_text(KML, encoding="utf-8")
    summary = import_file(db, path, source="kml", strict=True)
    assert summary.created == 1 and summary.rejected == 0
    assert len(summary.created_ids) == 1
    project = db.get(Project, summary.created_ids[0])
    assert project.registry_id == "VCS-900" and project.start_year == 2016
    assert project.name == "Reserva KML"


def test_strict_rejects_self_intersection(db, tmp_path):
    path = write_geojson(
        tmp_path / "p.geojson", [feature(BOWTIE, project_id="A1", start_year=2015)]
    )
    summary = import_file(db, path, source="test", strict=True)
    assert summary.created == 0 and summary.rejected == 1
    assert "no es válida" in summary.errors[0]
    assert "Self-intersection" in summary.errors[0]


def test_lenient_repairs_self_intersection(db, tmp_path):
    path = write_geojson(
        tmp_path / "p.geojson", [feature(BOWTIE, project_id="A1", start_year=2015)]
    )
    summary = import_file(db, path, source="test")
    assert summary.created == 1 and summary.repaired == 1


@pytest.mark.parametrize(
    ("properties", "reason"),
    [
        ({"project_name": "Sin id", "start_year": 2015}, "identificador"),
        ({"project_id": "B2", "project_name": "Sin fecha"}, "fecha de registro"),
    ],
)
def test_strict_requires_id_and_date(db, tmp_path, properties, reason):
    path = write_geojson(tmp_path / "p.geojson", [feature(RING, **properties)])
    summary = import_file(db, path, source="test", strict=True)
    assert summary.rejected == 1 and reason in summary.errors[0]


def test_strict_rejects_duplicates(db, tmp_path):
    path = write_geojson(tmp_path / "p.geojson", [feature(RING, project_id="C3", start_year=2015)])
    assert import_file(db, path, source="test", strict=True).created == 1
    second = import_file(db, path, source="test", strict=True)
    assert second.created == 0 and second.rejected == 1
    assert "C3 ya existe" in second.errors[0]


def test_unsupported_format(db, tmp_path):
    path = tmp_path / "datos.csv"
    path.write_text("a,b\n1,2\n")
    with pytest.raises(ValidationFailedError, match="formato no soportado"):
        import_file(db, path, source="test", strict=True)
