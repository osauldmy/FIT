"""Module for RedisJSON cache helper functions"""
import json
from typing import Optional, cast

from apixy.app import app
from apixy.entities.shared import JSON


async def json_set(key: str, data: JSON, expire: Optional[int] = None) -> None:
    await app.state.redis.execute("JSON.SET", key, ".", json.dumps(data))
    if expire:
        await app.state.redis.execute("EXPIRE", key, expire)


async def json_get(key: str) -> Optional[JSON]:
    if cached := await app.state.redis.execute("JSON.GET", key):
        return cast(JSON, json.loads(cached))
    return None
