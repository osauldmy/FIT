from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Literal, Optional, cast

import aiohttp
import databases
import jmespath
import motor.motor_asyncio
from pydantic import AnyUrl, Field, HttpUrl, validator

from apixy.entities.shared import JSONPathSerializable


class DataSource(JSONPathSerializable):
    """
    An interface for fetching data from a remote source

    :param url: URI (http(s), database etc)
    :param jsonpath: JMESPath (https://jmespath.org/) query string
    :param timeout: a float timeout value
    """

    url: AnyUrl
    jsonpath: str
    timeout: Optional[float] = Field(None, ge=0.0)

    @validator("jsonpath")
    @classmethod
    def validate_json_path(cls, value: str) -> jmespath.parser.ParsedResult:
        """Validator for jmespath strings"""
        try:
            return jmespath.compile(value)
        except jmespath.exceptions.ParseError as exception:
            raise ValueError("Invalid JsonPath") from exception

    @abstractmethod
    async def fetch_data(self) -> Dict[str, Any]:
        """Fetches data as defined by the instance's attributes"""


class HTTPDataSource(DataSource):
    """A datasource that fetches data from an external API."""

    url: HttpUrl
    method: Literal["GET", "POST", "PUT", "DELETE"]
    body: Dict[str, Any] = {}
    headers: Dict[str, Any] = {}

    async def fetch_data(self) -> Dict[str, Any]:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.request(
                method=self.method,
                url=self.url,
                json=self.body,
                headers=self.headers,
            ) as response:
                data = await response.json()

        return {
            "result": cast(jmespath.parser.ParsedResult, self.jsonpath).search(data)
        }


class MongoDBDataSource(DataSource):
    """A datasource that fetches data from a MongoDB collection."""

    database: str
    collection: str
    query: Dict[str, Any] = {}

    async def fetch_data(self) -> Dict[str, Any]:

        client = motor.motor_asyncio.AsyncIOMotorClient(self.url)
        cursor = client[self.database][self.collection].find(self.query)
        try:
            data = await cursor.to_list(None)
        finally:
            await cursor.close()

        return {
            "result": cast(jmespath.parser.ParsedResult, self.jsonpath).search(data)
        }


class SQLDataSource(DataSource):
    """A datasource that fetches data from SQL database."""

    query: str

    # TODO: sql validator (allow only select)

    async def fetch_data(self) -> Dict[str, Any]:
        async with databases.Database(self.url) as database:
            rows = await database.fetch_all(query=self.query)

        return {
            "result": cast(jmespath.parser.ParsedResult, self.jsonpath).search(
                [dict(row) for row in rows]
            )
        }
