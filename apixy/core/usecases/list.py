from apixy.core.entities import Project
from apixy.shared import Response

from .base import ProjectRepositoryUsecase


class ListProjectsUsecase(ProjectRepositoryUsecase[list[Project]]):
    """Usecase for a list of products"""

    async def execute(self) -> Response[list[Project]]:
        """Fetches Projects and returns them."""
        projects = await self.project_repository.getAll()
        return Response.success(content=projects)
