import asyncio
import logging
from typing import Any, Dict, List, Optional, Type, Union, cast

from pydantic import BaseModel, Field

from .datasource import (
    DataSourceFetchError,
    HTTPDataSource,
    MongoDBDataSource,
    SQLDataSource,
)
from .fetch_logger import FetchLogger
from .merge_strategy import MERGE_STRATEGY_MAPPING
from .proxy_response import ProxyResponse
from .shared import ForbidExtraModel, OmitFieldsConfig

logger = logging.getLogger(__name__)


class Project(ForbidExtraModel):
    """
    A Project will be accessible via its slug.
    Add DataSources to it to enable fetching via the proxy
    """

    id: Optional[int]
    name: str = Field(max_length=64)
    # the regex matches alphanumeric chars separated with hyphens
    # todo: we might want to do this without a regex
    slug: str = Field(max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")
    merge_strategy: str = Field(
        regex=r"^{}$".format("$|^".join(MERGE_STRATEGY_MAPPING.keys()))
    )
    description: Optional[str] = Field(default=None, max_length=512)

    class Config:
        orm_mode = True


class ProjectWithDataSources(Project):
    datasources: List[Union[HTTPDataSource, MongoDBDataSource, SQLDataSource]]

    async def fetch_data(self, fetch_logger: FetchLogger) -> ProxyResponse:

        fetched, errors = [], []
        fetch = (
            fetch_logger.fetch_timer(datasource.fetch_data)
            for datasource in self.datasources
        )
        gathered = await asyncio.gather(*fetch, return_exceptions=True)
        for index, (result, nanoseconds) in enumerate(gathered):
            if not isinstance(result, Exception):
                fetched.append(result)
                status = FetchLogger.FetchStatus.SUCCESS
            else:
                logger.exception(result)

                status = FetchLogger.FetchStatus.ERROR
                key = "{}: ({})".format(
                    self.datasources[index].name, self.datasources[index].url
                )

                if isinstance(result, asyncio.TimeoutError):
                    errors.append({key: "Timeout!"})
                    status = FetchLogger.FetchStatus.TIMEOUT
                elif isinstance(result, DataSourceFetchError):
                    errors.append({key: str(result) or "Fetch error!"})

            if self.datasources[index].id is not None:
                asyncio.create_task(
                    fetch_logger.save_log(
                        cast(int, self.datasources[index].id),
                        nanoseconds,
                        fetch_status=status,
                    )
                )

        merged = MERGE_STRATEGY_MAPPING[self.merge_strategy].apply(fetched)
        return ProxyResponse(
            result={
                "size": len(merged),
                "data": merged,
            },
            errors=None if len(errors) == 0 else {"size": len(errors), "data": errors},
        )


class ProjectInput(Project):
    """
    An input class for creating and modifying Projects.
    """

    class Config(OmitFieldsConfig, Project.Config):
        omit_fields = ("id",)

        @classmethod
        def schema_extra(cls, schema: Dict[str, Any], model: Type[BaseModel]) -> None:
            super().schema_extra(schema, model)
            schema.update(
                {
                    "example": {
                        "name": "Example project",
                        "slug": "example",
                        "merge_strategy": "concatenation",
                        "description": "This is an example project.",
                    }
                }
            )
