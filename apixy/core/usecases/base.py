from abc import abstractmethod
from typing import TypeVar

from apixy.core.entities import ProjectRepository
from apixy.shared import AppResponse, Usecase

T = TypeVar("T")
E = TypeVar("E")


class ProjectRepositoryUsecase(Usecase[T, E]):
    """Usecase base class which accepts a ProjectRepository."""

    project_repository: ProjectRepository

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    @abstractmethod
    async def execute(self, data: T) -> AppResponse[E]:
        pass
