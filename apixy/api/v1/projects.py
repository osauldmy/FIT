from typing import List

from fastapi import APIRouter

from apixy.core.entities.project import Project
from apixy.core.usecases.create import CreateProjectsUsecase
from apixy.core.usecases.list import (
    ListProjectsInput,
    ListProjectsOutput,
    ListProjectsUsecase,
)
from apixy.data.postgresql.repositories import PostgresProjectRepository

router = APIRouter(tags=["projects"])


@router.get("/")
async def get_projects(count: int, page: int) -> List[ListProjectsOutput]:
    """Endpoint for project list."""
    # instantiating this here, could later be moved into a decorator (for example)
    repo = PostgresProjectRepository()
    usecase = ListProjectsUsecase(project_repository=repo)
    response = await usecase.execute(ListProjectsInput(count=count, page=page))
    return response.content


@router.post("/")
async def create_project(project: Project) -> Project:
    """Endpoint for creating a project."""

    repo = PostgresProjectRepository()
    usecase = CreateProjectsUsecase(repo)
    response = await usecase.execute(project)
    return response.content
