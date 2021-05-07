"""The app's entrypoint"""
import logging

import aioredis
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from apixy import cache
from apixy.api.v1.app import app as v1_app
from apixy.config import SETTINGS, TORTOISE_CONFIG

app = FastAPI(title=SETTINGS.APP_NAME)
app.mount(SETTINGS.API_PREFIX + "/v1", v1_app)

register_tortoise(app, config=TORTOISE_CONFIG)


logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup() -> None:
    try:
        cache.REDIS = await aioredis.create_redis_pool(SETTINGS.REDIS_URI)
    except (OSError, AssertionError) as error:
        logger.exception(error)
        logger.error("Redis connection initializing failed!")


@app.on_event("shutdown")
async def shutdown() -> None:
    if cache.REDIS is not None:
        cache.REDIS.close()
        await cache.REDIS.wait_closed()
