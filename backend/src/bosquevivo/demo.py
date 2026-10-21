import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from bosquevivo.audit.service import AuditService
from bosquevivo.db.models import Project
from bosquevivo.satellite.models import Sensor
from bosquevivo.satellite.providers.fake import FakeProvider
from bosquevivo.satellite.service import SatelliteService


@dataclass(frozen=True)
class DemoSpec:
    registry_id: str
    name: str
    country: str
    lon: float
    lat: float
    expected_category: str
    drop_year: int | None = None
    loss_by_year: dict[int, float] | None = None
    valid_fraction: float = 0.9
    series_start: date = date(2016, 1, 1)
    base_ndvi: float = 0.8


DEMO_PROJECTS = (
    DemoSpec("DEMO-1", "Reserva El Roble", "Colombia", -75.60, 6.20, "Alta"),
    DemoSpec(
        "DEMO-2",
        "Finca La Aurora",
        "Colombia",
        -74.80,
        4.60,
        "Baja",
        drop_year=2021,
        loss_by_year={2021: 300.0, 2022: 180.0},
    ),
    DemoSpec(
        "DEMO-3",
        "Selva del Alto Putumayo",
        "Colombia",
        -76.60,
        0.90,
        "Insuficiente",
        valid_fraction=0.02,
        series_start=date(2023, 1, 1),
    ),
)

SIDE = 0.06


def polygon(lon: float, lat: float) -> dict:
    ring = [
        [lon, lat],
        [lon + SIDE, lat],
        [lon + SIDE, lat + SIDE],
        [lon, lat + SIDE],
        [lon, lat],
    ]
    return {"type": "Polygon", "coordinates": [ring]}


def seed_demo(session: Session, images_dir: Path, end: date = date(2024, 12, 31)) -> list[Project]:
    projects: list[Project] = []
    for spec in DEMO_PROJECTS:
        project = Project(
            source_registry="demo",
            registry_id=spec.registry_id,
            name=spec.name,
            country=spec.country,
            project_type="REDD+",
            start_year=2018,
            area_ha=4400.0,
            geometry=json.dumps(polygon(spec.lon, spec.lat)),
            source="datos de demostración",
            source_version="demo-1",
        )
        session.add(project)
        session.flush()
        provider = FakeProvider(
            base_ndvi=spec.base_ndvi,
            drop_year=spec.drop_year,
            loss_by_year=spec.loss_by_year,
            valid_fraction=spec.valid_fraction,
        )
        satellite = SatelliteService(session, provider, images_dir)
        satellite.refresh_timeseries(
            project.id, spec.series_start, end, sensors=(Sensor.SENTINEL2,)
        )
        satellite.refresh_forest_loss(project.id)
        AuditService(session, dataset_versions=provider.dataset_versions()).run(project.id)
        projects.append(project)
    session.flush()
    return projects
