from typing import Dict

from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from apixy.shared import AppResponse

from .base import ProjectRepositoryUsecase


@dataclass(frozen=True)
class Input:
    """Container for the input parameters this usecase accepts"""

    filters: Dict[str, str]
    count: int
    page: int


class OutputProject(BaseModel):
    """This is what the usecase will output"""

    slug: str


class ListProjectsUsecase(ProjectRepositoryUsecase[Input, list[OutputProject]]):
    """Usecase for a list of products"""

    async def execute(self, data: Input) -> AppResponse[list[OutputProject]]:
        """Fetches Projects and returns them."""
        projects = await self.project_repository.get_all(filters=data.filters)
        return AppResponse.success(
            content=[OutputProject(slug=p.slug) for p in projects]
        )
