import hashlib
import json
from datetime import date
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from bosquevivo.core.errors import NotFoundError
from bosquevivo.db.models import (
    ForestBaselineRecord,
    ForestLoss,
    ImageAsset,
    NdviObservation,
    Project,
)
from bosquevivo.satellite.models import Sensor, ThumbnailKind
from bosquevivo.satellite.provider import SatelliteProvider

SENTINEL2_START = date(2017, 1, 1)
LANDSAT_START = date(1999, 1, 1)


class SatelliteService:
    def __init__(self, session: Session, provider: SatelliteProvider, images_dir: Path) -> None:
        self.session = session
        self.provider = provider
        self.images_dir = images_dir

    def _project(self, project_id: int) -> Project:
        project = self.session.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"proyecto {project_id} no existe")
        return project

    def refresh_timeseries(
        self, project_id: int, start: date, end: date, sensors: tuple[Sensor, ...] | None = None
    ) -> int:
        project = self._project(project_id)
        geometry = json.loads(project.geometry)
        chosen = sensors or (Sensor.LANDSAT, Sensor.SENTINEL2)
        stored = 0
        for sensor in chosen:
            floor = SENTINEL2_START if sensor == Sensor.SENTINEL2 else LANDSAT_START
            sensor_start = max(start, floor)
            if sensor_start >= end:
                continue
            points = self.provider.get_timeseries(geometry, sensor_start, end, sensor)
            self.session.execute(
                delete(NdviObservation).where(
                    NdviObservation.project_id == project_id,
                    NdviObservation.sensor == sensor.value,
                    NdviObservation.period >= sensor_start,
                    NdviObservation.period <= end,
                )
            )
            for point in points:
                self.session.add(
                    NdviObservation(
                        project_id=project_id,
                        period=point.period,
                        sensor=point.sensor.value,
                        ndvi_mean=point.ndvi_mean,
                        ndvi_p10=point.ndvi_p10,
                        ndvi_p90=point.ndvi_p90,
                        valid_fraction=point.valid_fraction,
                        scene_count=point.scene_count,
                    )
                )
            stored += len(points)
        self.session.flush()
        return stored

    def refresh_forest_loss(self, project_id: int) -> int:
        project = self._project(project_id)
        geometry = json.loads(project.geometry)
        points = self.provider.get_forest_loss(geometry)
        baseline = self.provider.get_forest_baseline(geometry)
        self.session.execute(delete(ForestLoss).where(ForestLoss.project_id == project_id))
        self.session.execute(
            delete(ForestBaselineRecord).where(ForestBaselineRecord.project_id == project_id)
        )
        self.session.add(
            ForestBaselineRecord(
                project_id=project_id,
                tree_cover_ha=baseline.tree_cover_ha,
                threshold_percent=baseline.threshold_percent,
                source=baseline.source,
            )
        )
        for point in points:
            self.session.add(
                ForestLoss(
                    project_id=project_id,
                    year=point.year,
                    ha_lost=point.ha_lost,
                    source=point.source,
                )
            )
        self.session.flush()
        return len(points)

    def thumbnail(
        self,
        project_id: int,
        start: date,
        end: date,
        kind: ThumbnailKind = ThumbnailKind.NATURAL,
        sensor: Sensor = Sensor.SENTINEL2,
    ) -> ImageAsset:
        project = self._project(project_id)
        existing = (
            self.session.query(ImageAsset)
            .filter_by(
                project_id=project_id,
                start_date=start,
                end_date=end,
                kind=kind.value,
                sensor=sensor.value,
            )
            .first()
        )
        if existing and Path(existing.path).exists():
            return existing
        content = self.provider.get_thumbnail(
            json.loads(project.geometry), start, end, kind, sensor
        )
        folder = self.images_dir / str(project_id)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{kind.value}_{sensor.value}_{start.isoformat()}_{end.isoformat()}.png"
        path.write_bytes(content)
        asset = existing or ImageAsset(
            project_id=project_id,
            start_date=start,
            end_date=end,
            sensor=sensor.value,
            kind=kind.value,
            path=str(path),
            sha256=hashlib.sha256(content).hexdigest(),
        )
        asset.path = str(path)
        asset.sha256 = hashlib.sha256(content).hexdigest()
        self.session.add(asset)
        self.session.flush()
        return asset
