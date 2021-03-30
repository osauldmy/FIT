import uuid
from typing import Any, Dict, List, Optional

from apixy.core import Project, ProjectRepository

from .postgres import PostgresRepository


class PostgresProjectRepository(PostgresRepository, ProjectRepository):
    """Repository implementation for Project entities."""

    async def getById(self, project_id: uuid.UUID) -> Project:
        # get project through sqlalchemy
        pass

    async def getAll(self, filters: Optional[Dict[str, Any]] = None) -> List[Project]:
        return [Project(uuid=uuid.uuid4(), slug="dummy_project")]

    async def save(self, project: Project) -> None:
        pass
