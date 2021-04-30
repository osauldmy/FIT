import asyncio
import logging
from typing import List, Optional, Union

from pydantic import Field

from .datasource import (
    DataSourceFetchError,
    HTTPDataSource,
    MongoDBDataSource,
    SQLDataSource,
)
from .merge_strategy import MERGE_STRATEGY_MAPPING
from .proxy_response import ProxyResponse
from .shared import ForbidExtraModel, OmitFieldsConfig

logger = logging.getLogger(__name__)


class Project(ForbidExtraModel):
    id: Optional[int]
    name: str = Field(max_length=64)
    slug: str = Field(max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")
    merge_strategy: str = Field(regex=r"|".join(MERGE_STRATEGY_MAPPING.keys()))
    # the regex matches alphanumeric chars separated with hyphens
    # todo: we might want to do this without a regex
    description: Optional[str] = Field(default=None, max_length=512)

    class Config:
        orm_mode = True


class ProjectWithDataSources(Project):
    datasources: List[Union[HTTPDataSource, MongoDBDataSource, SQLDataSource]]

    async def fetch_data(self) -> ProxyResponse:

        fetched, errors = [], []

        for datasource in self.datasources:
            try:
                fetched.append(await datasource.fetch_data())
            # TODO: `datasource.url` -> `datasource.name` after caching MR merge.
            except asyncio.TimeoutError as error:
                logger.exception(error)
                errors.append({datasource.url: "Timeout!"})
            except DataSourceFetchError:
                errors.append({datasource.url: "Fetch error!"})

        merged = MERGE_STRATEGY_MAPPING[self.merge_strategy].apply(fetched)
        return ProxyResponse(
            result={
                "size": len(merged),
                "data": merged,
            },
            errors={"size": len(errors), "data": errors},
        )


class ProjectInput(Project):
    class Config(OmitFieldsConfig, Project.Config):
        omit_fields = ("id",)
