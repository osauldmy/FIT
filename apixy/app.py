"""The app's entrypoint"""
import aioredis
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from apixy.api.v1.app import app as v1_app
from apixy.config import SETTINGS, TORTOISE_CONFIG

app = FastAPI(title=SETTINGS.APP_NAME)
app.mount(SETTINGS.API_PREFIX + "/v1", v1_app)

register_tortoise(app, config=TORTOISE_CONFIG)


@app.on_event("startup")
async def startup() -> None:
    app.state.redis = await aioredis.create_redis_pool(SETTINGS.REDIS_URI)


@app.on_event("shutdown")
async def shutdown() -> None:
    app.state.redis.close()
    await app.state.redis.wait_closed()
