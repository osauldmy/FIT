from typing import List

from fastapi import APIRouter

from apixy.core.entities import Project
from apixy.core.usecases import ListProjectsUsecase
from apixy.data.postgresql.repositories import PostgresProjectRepository

router = APIRouter()


@router.get("/")
async def get_projects() -> List[Project]:
    """Endpoint for project list."""
    # instantiating this here, could later be moved into a decorator (for example)
    repo = PostgresProjectRepository()
    async with repo:
        uc = ListProjectsUsecase(project_repository=repo)
        response = await uc.execute()
    return response.content
