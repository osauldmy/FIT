"""The app's entrypoint"""
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from apixy.api.v1.app import app as v1_app
from apixy.config import TORTOISE_CONFIG, settings

app = FastAPI(title=settings.APP_NAME)
app.mount(settings.API_PREFIX + "/v1", v1_app)

register_tortoise(app, config=TORTOISE_CONFIG)
