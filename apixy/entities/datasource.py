from __future__ import annotations

import logging
import socket
from abc import abstractmethod
from typing import Annotated, Any, Dict, Final, Literal, Mapping, Optional, Type, Union
from urllib.parse import urlparse

import aiohttp
import async_timeout
import databases
import jmespath
import motor.motor_asyncio
import sqlparse
from pydantic import AnyUrl, BaseModel, Field, HttpUrl, validator

from apixy.cache import redis_cache
from apixy.config import SETTINGS
from apixy.entities.shared import ForbidExtraModel, OmitFieldsConfig

from .validators import validate_nonzero_length

logger = logging.getLogger(__name__)


class DataSourceFetchError(Exception):
    """
    Unified exception for datasource fetch method to raise in case of fetching failure.
    To be caught by Project.fetch_data()
    """


class DataSource(ForbidExtraModel):
    """
    An interface for fetching data from a remote source

    :param name: datasource name for displaying/caching purposes
    :param url: URI (http(s), database etc)
    :param jsonpath: JMESPath (https://jmespath.org/) query string
    :param timeout: a float timeout value (in seconds)
    :param cache_expire: an int value for cache expiration time (in seconds).
                         Does not expire if 0.
    """

    class Config:
        orm_mode = True

    id: Optional[int]
    type: str
    name: str
    url: AnyUrl
    jsonpath: str
    timeout: Optional[float] = Field(60, gt=0.0)
    cache_expire: Optional[int] = Field(None, ge=0)

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
    async def fetch_data(self) -> Any:
        """
        Fetches data as defined by the instance's attributes

        :raises asyncio.exceptions.TimeoutError: on timeout
        :raises DataSourceFetchError: on inability to fetch data or some another
                                      fetch-related problem
        """


class HTTPDataSource(DataSource):
    """A datasource that fetches data from an external API."""

    url: HttpUrl
    method: Literal["GET", "POST", "PUT", "DELETE"]
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    type: Annotated[str, Field(regex=r"^http$")] = "http"

    _body_headers_not_empty = validator("body", "headers", allow_reuse=True)(
        validate_nonzero_length
    )

    @redis_cache
    async def fetch_data(self) -> Any:
        async with async_timeout.timeout(self.timeout):
            try:
                async with aiohttp.request(
                    method=self.method,
                    url=self.url,
                    json=self.body,
                    headers=self.headers,
                ) as response:
                    data = await response.json()
            except aiohttp.ClientError as error:
                logger.exception(error)
                raise DataSourceFetchError from error

        return jmespath.search(self.jsonpath, data)


class MongoDBDataSource(DataSource):
    """A datasource that fetches data from a MongoDB collection."""

    database: str
    collection: str
    query: Dict[str, Any] = {}
    type: Annotated[str, Field(regex=r"^mongo$")] = "mongo"

    @redis_cache
    async def fetch_data(self) -> Any:
        client = motor.motor_asyncio.AsyncIOMotorClient(self.url)
        async with async_timeout.timeout(self.timeout):
            cursor = client[self.database][self.collection].find(
                self.query, {"_id": False}
            )
            try:
                data = await cursor.to_list(None)
            finally:
                await cursor.close()

        return jmespath.search(self.jsonpath, data)


class SQLDataSource(DataSource):
    """A datasource that fetches data from SQL database."""

    query: str
    type: Annotated[str, Field(regex=r"^sql$")] = "sql"

    @validator("url")
    @classmethod
    def validate_url(cls, url: str) -> str:
        """Validator for sql database url"""
        parsed_url = urlparse(url)

        if parsed_url.hostname in (
            "localhost",
            "127.0.0.1",
            "0.0.0.0",  # nosec
            SETTINGS.POSTGRES_HOST,
        ):
            raise ValueError("SQL database url cannot be localhost address")

        localhost = socket.gethostname()
        forbidden_addresses = socket.getaddrinfo(localhost, SETTINGS.POSTGRES_PORT)
        if SETTINGS.POSTGRES_HOST not in (
            "",
            "localhost",
            "127.0.0.1",
            "0.0.0.0",  # nosec
        ):
            forbidden_addresses.extend(
                socket.getaddrinfo(SETTINGS.POSTGRES_HOST, SETTINGS.POSTGRES_PORT)
            )

        try:
            target_address = socket.getaddrinfo(parsed_url.hostname, parsed_url.port)
        except socket.gaierror as socket_error:
            raise ValueError("Invalid destination url") from socket_error
        for (_, _, _, _, socket_address) in forbidden_addresses:
            for (_, _, _, _, r_socket_address) in target_address:
                if r_socket_address[0] == socket_address[0]:
                    raise ValueError("SQL database url cannot be localhost address")

        return url

    @validator("query")
    @classmethod
    def validate_query(cls, query: str) -> str:
        """Validator for query"""
        statements = sqlparse.parse(query)

        if len(statements) != 1:
            raise ValueError("Query must contain only one statement")

        if statements[0].get_type() != "SELECT":
            raise ValueError("Query can be only SELECT statement")

        return query

    @redis_cache
    async def fetch_data(self) -> Any:
        async with async_timeout.timeout(self.timeout):
            try:
                async with databases.Database(self.url) as database:
                    rows = await database.fetch_all(query=self.query)
            except RuntimeError as error:
                logger.exception(error)
                raise DataSourceFetchError from error

        return jmespath.search(self.jsonpath, [dict(row) for row in rows])


class HTTPDataSourceInput(HTTPDataSource):
    class Config(OmitFieldsConfig, DataSource.Config):
        omit_fields = ("id",)

        @classmethod
        def schema_extra(cls, schema: Dict[str, Any], model: Type[BaseModel]) -> None:
            super().schema_extra(schema, model)
            schema.update(
                {
                    "example": {
                        "url": "https://example.org/api",
                        "jsonpath": "*",
                        "timeout": 60,
                        "type": "http",
                        "method": "GET",
                        "body": {"field": "value"},
                        "headers": {"Authorization": "Basic 123-AUTH-TOKEN"},
                    }
                }
            )


class MongoDBDataSourceInput(MongoDBDataSource):
    class Config(OmitFieldsConfig, DataSource.Config):
        omit_fields = ("id",)

        @classmethod
        def schema_extra(cls, schema: Dict[str, Any], model: Type[BaseModel]) -> None:
            super().schema_extra(schema, model)
            schema.update(
                {
                    "example": {
                        "name": "mongo",
                        "url": "mongodb+srv://cluster-0.foo.mongodb.net/example",
                        "jsonpath": "*",
                        "database": "foo",
                        "collection": "bar",
                        "query": {"a": "b"},
                    }
                }
            )


class SQLDataSourceInput(SQLDataSource):
    class Config(OmitFieldsConfig, DataSource.Config):
        omit_fields = ("id",)

        @classmethod
        def schema_extra(cls, schema: Dict[str, Any], model: Type[BaseModel]) -> None:
            super().schema_extra(schema, model)
            schema.update(
                {
                    "example": {
                        "name": "sql",
                        "url": "postgresql://pepega@localhost",
                        "timeout": 20,
                        "jsonpath": "[*]",
                        "query": "SELECT * FROM table;",
                    }
                }
            )


class DataSourceUnion(BaseModel):
    __root__: Union[HTTPDataSource, MongoDBDataSource, SQLDataSource]


DataSourceInput = Union[HTTPDataSourceInput, MongoDBDataSourceInput, SQLDataSourceInput]

DATA_SOURCES: Final[Mapping[str, Type[DataSource]]] = {
    "http": HTTPDataSource,
    "mongo": MongoDBDataSource,
    "sql": SQLDataSource,
}
