"""Module for RedisJSON cache helper functions"""
import json
from functools import wraps
from typing import Any, Dict

from apixy.app import app


def redis_cache(coroutine_method: Any) -> Any:
    """
    A decorator to enforce DRY on caching for datasources.
    """

    @wraps(coroutine_method)
    async def wrapper(self: Any) -> Dict[str, Any]:
        """
        Caching routines.
        """
        if (
            self.cache_expire is not None
            and self.cache_expire >= 0
            and (cached := await app.state.redis.get(self.name))
        ):
            return {"result": json.loads(cached)}

        data: Dict[str, Any] = await coroutine_method(self)

        if self.cache_expire is not None and self.cache_expire >= 0:
            await app.state.redis.set(
                self.name, json.dumps(data["result"]), expire=self.cache_expire
            )

        return data

    return wrapper
