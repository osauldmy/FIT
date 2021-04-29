from __future__ import annotations

from abc import abstractmethod
from typing import Annotated, Any, Dict, Final, Literal, Mapping, Optional, Type, Union

import aiohttp
import async_timeout
import databases
import jmespath
import motor.motor_asyncio
from pydantic import AnyUrl, BaseModel, Field, HttpUrl, validator

from apixy.entities.shared import ForbidExtraModel, OmitFieldsConfig


class DataSource(ForbidExtraModel):
    """
    An interface for fetching data from a remote source

    :param url: URI (http(s), database etc)
    :param jsonpath: JMESPath (https://jmespath.org/) query string
    :param timeout: a float timeout value (in seconds)

    :raises asyncio.exceptions.TimeoutError: on timeout
    """

    class Config:
        orm_mode = True

    id: Optional[int]
    url: AnyUrl
    jsonpath: str
    timeout: Optional[float] = Field(None, gt=0.0)
    type: str

    @validator("jsonpath")
    @classmethod
    def validate_json_path(cls, value: str) -> str:
        """Validator for jmespath strings"""
        try:
            jmespath.compile(value)
            return value
        except jmespath.exceptions.ParseError as exception:
            raise ValueError("Invalid JsonPath") from exception

    @abstractmethod
    async def fetch_data(self) -> Dict[str, Any]:
        """Fetches data as defined by the instance's attributes"""


class HTTPDataSource(DataSource):
    """A datasource that fetches data from an external API."""

    url: HttpUrl
    method: Literal["GET", "POST", "PUT", "DELETE"]
    body: Optional[Dict[str, Any]]
    headers: Optional[Dict[str, Any]]
    type: Annotated[str, Field(regex="http")] = "http"

    async def fetch_data(self) -> Dict[str, Any]:
        async with async_timeout.timeout(self.timeout):
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=self.method,
                    url=self.url,
                    json=self.body,
                    headers=self.headers,
                ) as response:
                    data = await response.json()

        return {"result": jmespath.compile(self.jsonpath).search(data)}


class MongoDBDataSource(DataSource):
    """A datasource that fetches data from a MongoDB collection."""

    database: str
    collection: str
    query: Dict[str, Any] = {}
    type: Annotated[str, Field(regex="mongo")] = "mongo"

    async def fetch_data(self) -> Dict[str, Any]:
        client = motor.motor_asyncio.AsyncIOMotorClient(self.url)
        cursor = client[self.database][self.collection].find(self.query)
        try:
            async with async_timeout.timeout(self.timeout):
                data = await cursor.to_list(None)
        finally:
            await cursor.close()

        return {"result": jmespath.compile(self.jsonpath).search(data)}


class SQLDataSource(DataSource):
    """A datasource that fetches data from SQL database."""

    query: str
    type: Annotated[str, Field(regex="sql")] = "sql"

    # TODO: sql validator (allow only select)

    async def fetch_data(self) -> Dict[str, Any]:
        async with async_timeout.timeout(self.timeout):
            async with databases.Database(self.url) as database:
                rows = await database.fetch_all(query=self.query)

        return {
            "result": jmespath.compile(self.jsonpath).search(
                [dict(row) for row in rows]
            )
        }


class HTTPDataSourceInput(HTTPDataSource):
    class Config(OmitFieldsConfig, DataSource.Config):
        omit_fields = ("id",)


class MongoDBDataSourceInput(MongoDBDataSource):
    class Config(OmitFieldsConfig, DataSource.Config):
        omit_fields = ("id",)


class SQLDataSourceInput(SQLDataSource):
    class Config(OmitFieldsConfig, DataSource.Config):
        omit_fields = ("id",)


class DataSourceUnion(BaseModel):
    __root__: Union[HTTPDataSource, MongoDBDataSource, SQLDataSource]


DataSourceInput = Union[HTTPDataSourceInput, MongoDBDataSourceInput, SQLDataSourceInput]

DATA_SOURCES: Final[Mapping[str, Type[DataSource]]] = {
    "http": HTTPDataSource,
    "mongo": MongoDBDataSource,
    "sql": SQLDataSource,
}
