from fastapi import APIRouter

from .endpoints import projects

router = APIRouter()
router.include_router(projects.router, prefix="/projects")
