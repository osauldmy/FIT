import uuid
from typing import Any, Dict, List, Optional

from apixy.core import Project, ProjectRepository

from ..models.core import Project as ProjectModel


class PostgresProjectRepository(ProjectRepository):
    """Repository implementation for Project entities."""

    @staticmethod
    def map_to_project(model: ProjectModel) -> Project:
        """Creates a Project instance from the DB model."""
        return Project(slug=model.slug, uuid=model.uuid)

    async def get_by_id(self, project_id: uuid.UUID) -> Project:
        # get project through sqlalchemy
        pass

    async def get_all(
        self, count: int = 30, page: int = 1, filters: Optional[Dict[str, Any]] = None
    ) -> List[Project]:
        return [self.map_to_project(p) for p in await ProjectModel.all()]

    async def save(self, project: Project) -> None:
        pass
