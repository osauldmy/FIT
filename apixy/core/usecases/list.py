from apixy.core.entities import Project
from apixy.shared import AppResponse

from .base import ProjectRepositoryUsecase


class ListProjectsUsecase(ProjectRepositoryUsecase[list[Project]]):
    """Usecase for a list of products"""

    async def execute(self) -> AppResponse[list[Project]]:
        """Fetches Projects and returns them."""
        projects = await self.project_repository.get_all()
        return AppResponse.success(content=projects)
