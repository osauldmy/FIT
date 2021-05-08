import asyncio
import logging
import time
from functools import wraps
from typing import Any, Awaitable, Callable, List, Optional, Tuple, Union, cast, Union, List, Optional

from pydantic import BaseModel, Field

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


class FetchLogger:
    async def save_log(
        self, datasource_id: int, nanoseconds: int, success: bool
    ) -> None:
        raise NotImplementedError()

    @staticmethod
    async def fetch_timer(coroutine: Callable[[], Awaitable[Any]]) -> Any:
        @wraps(coroutine)
        async def wrapped() -> Tuple[Any, int]:
            time_start = time.perf_counter_ns()
            result = await coroutine()
            time_measured = time.perf_counter_ns() - time_start
            return result, time_measured

        return wrapped


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

        gathered = await asyncio.gather(
            *(
                fetch_logger.fetch_timer(datasource.fetch_data)
                for datasource in self.datasources
            ),
            return_exceptions=True
        )

        for index, (result, nanoseconds) in enumerate(gathered):
            if not isinstance(result, Exception):
                fetched.append(result)
                success = True
            else:
                logger.exception(result)
                success = False
                # TODO: `datasource.url` -> `datasource.name` after caching MR merge.
                if isinstance(result, asyncio.TimeoutError):
                    errors.append({self.datasources[index].url: "Timeout!"})
                elif isinstance(result, DataSourceFetchError):
                    errors.append({self.datasources[index].url: "Fetch error!"})

            if self.datasources[index].id is None:
                raise ValueError("DataSource has no ID.")
            asyncio.create_task(
                fetch_logger.save_log(
                    cast(int, self.datasources[index].id), nanoseconds, success=success
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
