from fastapi import FastAPI

from apixy.config import settings

from . import projects

app = FastAPI(title=settings.APP_NAME)
app.include_router(projects.router, prefix="/projects")
