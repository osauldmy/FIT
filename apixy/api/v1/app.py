from fastapi import FastAPI

from . import projects

app = FastAPI()
app.include_router(projects.router, prefix="/projects")
