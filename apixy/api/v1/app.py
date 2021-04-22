from fastapi import FastAPI

from apixy.config import SETTINGS

from . import projects

app = FastAPI(title=SETTINGS.APP_NAME)
app.include_router(projects.router)
