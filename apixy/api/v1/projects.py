from typing import List

from fastapi import APIRouter

from apixy.entities.project import Project

router = APIRouter(tags=["projects"])


@router.get("/")
async def get_projects() -> List[Project]:
    """Endpoint for project list."""
    return []  # FIXME


@router.post("/")
async def create_project(project: Project) -> Project:
    """Endpoint for creating a project."""
    return project  # FIXME
