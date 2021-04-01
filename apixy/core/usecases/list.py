from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from apixy.shared import UseCaseResponse

from .base import ProjectRepositoryUsecase


@dataclass(frozen=True)
class ListProjectsInput:
    """Container for the input parameters this usecase accepts"""

    count: int
    page: int


class ListProjectsOutput(BaseModel):
    """This is what the usecase will output"""

    slug: str


class ListProjectsUsecase(
    ProjectRepositoryUsecase[ListProjectsInput, list[ListProjectsOutput]]
):
    """Usecase for a list of products"""

    async def execute(
        self, data: ListProjectsInput
    ) -> UseCaseResponse[list[ListProjectsOutput]]:
        """Fetches Projects and returns them."""

        projects = await self.project_repository.get_all(
            count=data.count, page=data.page
        )
        result = [ListProjectsOutput(slug=p.slug) for p in projects]
        return UseCaseResponse.success(content=result)
