from apixy.shared import UseCaseResponse

from ..entities import Project
from .base import ProjectRepositoryUsecase


class CreateProjectsUsecase(ProjectRepositoryUsecase[Project, Project]):
    """Creates a project."""

    async def execute(self, data: Project) -> UseCaseResponse[Project]:

        project = await self.project_repository.save(data)
        return UseCaseResponse.success(content=project)
