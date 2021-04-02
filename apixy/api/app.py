from fastapi import FastAPI

from apixy.config import settings

from .v1.app import app as v1_app

app = FastAPI(title="Apixy")
app.mount(settings.API_PREFIX + "/v1", v1_app)
