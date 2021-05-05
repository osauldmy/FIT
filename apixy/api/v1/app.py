from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apixy.config import SETTINGS

from . import datasources, fetch, projects

app = FastAPI(title=SETTINGS.APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.ORIGINS,
    allow_credentials=True,
    allow_methods=SETTINGS.ORIGINS_METHODS,
    allow_headers=SETTINGS.ORIGINS_HEADERS,
)
app.include_router(projects.router)
app.include_router(datasources.router)
app.include_router(fetch.router)
