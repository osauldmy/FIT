from __future__ import annotations

# from abc import abstractmethod
from typing import Any, Dict, Literal, Optional

# import aiohttp
# import databases
import jmespath

# from motor import motor_asyncio
from pydantic import AnyUrl, BaseConfig, BaseModel, HttpUrl

from apixy.shared.entities import ForbidExtraModel


# todo: will we need this anywhere else? if so, move it to shared
class JSONPathSerializable(BaseModel):
    """Adds a jmespath json encoder to the model."""

    class Config(BaseConfig):
        """pydantic config"""

        json_encoders = {jmespath.parser.ParsedResult: lambda x: x.expression}


class DataSource(ForbidExtraModel, JSONPathSerializable):
    """An interface for fetching data from a remote source"""

    url: AnyUrl
    jsonpath: str
    # transformation/aggregation TODO
    timeout: Optional[float] = None  # TODO

    class Config(ForbidExtraModel.Config, JSONPathSerializable.Config):
        """pydantic config class"""

    # @validator("jsonpath")
    # def validate_json_path(cls: DataSource, v: str) -> jmespath.parser.ParsedResult:
    #     """Validator for jmespath strings"""
    #     try:
    #         return jmespath.compile(v)
    #     except jmespath.exceptions.ParseError:
    #         raise ValueError("Invalid JsonPath")

    # @abstractmethod
    # async def fetch_data(self) -> Dict[str, Any]:
    #     """Fetches data as defined by the instance's attributes"""


class HTTPDataSource(DataSource):
    """A datasource that fetches data from an external API."""

    url: HttpUrl
    method: Literal["GET", "POST", "PUT", "DELETE"]  # etc: TODO
    body: Dict[str, Any] = {}
    headers: Dict[str, Any] = {}
    # TODO: credentials/token # or leave in headers?

    # async def fetch_data(self) -> Dict[str, Any]:
    #     try:
    #         async with aiohttp.ClientSession(
    #             timeout=aiohttp.ClientTimeout(total=self.timeout)
    #         ) as session:
    #             async with session.request(
    #                 method=self.method,
    #                 url=self.url,
    #                 json=self.body,
    #                 headers=self.headers,
    #             ) as response:
    #                 data = await response.json()
    #
    #         return {
    #             "result": cast(
    #                 jmespath.parser.ParsedResult, self.jsonpath
    #             ).search(data)
    #         }
    #     except Exception as e:
    #         print(e)
    #         return {"result": f"fail:  {e}"}


class MongoDBDataSource(DataSource):
    """A datasource that fetches data from a MongoDB collection."""

    database: str
    collection: str
    query: Dict[str, Any]

    # async def fetch_data(self) -> Dict[str, Any]:
    #
    #     client = motor_asyncio.AsyncIOMotorClient(self.url)
    #     cursor = client[self.database][self.collection].find(self.query)
    #     data = await cursor.to_list()
    #
    #     try:
    #         return {
    #             "result": cast(
    #                 jmespath.parser.ParsedResult, self.jsonpath
    #             ).search(data)
    #         }
    #     except Exception as e:
    #         print(e)
    #         return {"result": f"fail:  {e}"}


class SQLDataSource(DataSource):
    """A datasource that fetches data from SQL database."""

    query: str

    # TODO: sql validator (allow only select)

    # async def fetch_data(self) -> Dict[str, Any]:
    #     try:
    #         async with databases.Database(self.url) as database:
    #             rows = await database.fetch_all(query=self.query)
    #
    #         return {
    #             "result": cast(jmespath.parser.ParsedResult, self.jsonpath).search(
    #                 [dict(row) for row in rows]
    #             )
    #         }
    #     except Exception as e:
    #         print(e)
    #         return {"result": f"fail:  {e}"}
