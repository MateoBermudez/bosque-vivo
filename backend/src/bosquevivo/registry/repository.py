import json
from collections.abc import Sequence

from shapely.geometry import Point, shape
from shapely.strtree import STRtree
from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.db.models import Project


class ProjectRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, project_id: int) -> Project | None:
        return self.session.get(Project, project_id)

    def find_by_registry(self, source_registry: str, registry_id: str) -> Project | None:
        stmt = select(Project).where(
            Project.source_registry == source_registry, Project.registry_id == registry_id
        )
        return self.session.scalars(stmt).first()

    def list_projects(
        self, country: str | None = None, limit: int = 100, offset: int = 0
    ) -> Sequence[Project]:
        stmt = select(Project).order_by(Project.name).limit(limit).offset(offset)
        if country:
            stmt = stmt.where(Project.country == country)
        return self.session.scalars(stmt).all()

    def all(self) -> Sequence[Project]:
        return self.session.scalars(select(Project)).all()

    def upsert(self, data: dict) -> tuple[Project, bool]:
        existing = self.find_by_registry(data["source_registry"], data["registry_id"])
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            return existing, False
        project = Project(**data)
        self.session.add(project)
        return project, True

    def _index(self) -> tuple[Sequence[Project], list, STRtree] | None:
        projects = self.all()
        if not projects:
            return None
        geoms = [shape(json.loads(p.geometry)) for p in projects]
        return projects, geoms, STRtree(geoms)

    def locate(self, lat: float, lon: float) -> Project | None:
        index = self._index()
        if index is None:
            return None
        projects, _, tree = index
        hits = tree.query(Point(lon, lat), predicate="intersects")
        return projects[int(hits[0])] if len(hits) else None

    def nearest(self, lat: float, lon: float) -> tuple[Project, float] | None:
        index = self._index()
        if index is None:
            return None
        projects, geoms, tree = index
        point = Point(lon, lat)
        position = int(tree.nearest(point))
        return projects[position], float(geoms[position].distance(point))
