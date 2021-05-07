import json
from unittest.mock import patch

import aioresponses
import fakeredis.aioredis
import pytest

from apixy import app
from apixy.entities.datasource import HTTPDataSource


@pytest.fixture
def http_datasource() -> HTTPDataSource:
    return HTTPDataSource(
        name="http",
        url="http://foo.bar",
        method="GET",
        jsonpath="[*]",
        timeout=1,
        cache_expire=None,
    )


@pytest.fixture
async def redis() -> fakeredis.aioredis.FakeConnectionsPool:
    try:
        pool = await fakeredis.aioredis.create_redis_pool()
        yield pool
    finally:
        pool.close()
        await pool.wait_closed()


@pytest.mark.parametrize(
    "redis_uri",
    (
        "",  # empty
        "http://localhost",  # bad scheme
        "sqlite:///foo.bar",  # bad scheme
        "redis://",  # missing url
        # other options, but nevertheless redis now is not running,
        # so it will catch anything
        "redis://redis:123",
        "redis://redis:6379",
    ),
)
@pytest.mark.asyncio
async def test_bad_redis_uri(redis_uri: str) -> None:
    with patch("apixy.config.SETTINGS.REDIS_URI", redis_uri):
        # won't raise as this is handled,
        # but logging will catch this
        await app.startup()


@pytest.mark.asyncio
async def test_cache_disabled(
    http_datasource: HTTPDataSource, redis: fakeredis.aioredis.FakeConnectionsPool
) -> None:
    with patch("apixy.cache.REDIS", redis):
        with aioresponses.aioresponses() as http_mock:
            http_mock.add(
                url=http_datasource.url,
                method=http_datasource.method,
                status=200,
                payload=["foo", "bar"],
            )
            data = await http_datasource.fetch_data()
        cached = await redis.get(http_datasource.name)

    assert cached != data
    assert cached is None


@pytest.mark.asyncio
async def test_cache_enabled_mock(
    http_datasource: HTTPDataSource, redis: fakeredis.aioredis.FakeConnectionsPool
) -> None:
    http_datasource.cache_expire = 10
    with patch("apixy.cache.REDIS", redis):
        with aioresponses.aioresponses() as http_mock:
            http_mock.add(
                url=http_datasource.url,
                method=http_datasource.method,
                status=200,
                payload=["foo", "bar"],
            )
            data = await http_datasource.fetch_data()

        assert json.loads(await redis.get(http_datasource.name)) == data
