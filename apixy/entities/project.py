import asyncio
import logging
import traceback
from typing import List, Optional, Union

from pydantic import Field

from .datasource import HTTPDataSource, MongoDBDataSource, SQLDataSource
from .merge_strategy import MERGE_STRATEGY_MAPPING
from .proxy_response import ProxyResponse
from .shared import ForbidExtraModel, OmitFieldsConfig


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

    async def fetch_data(
        self, include_exceptions: bool = True, include_tracebacks: bool = False
    ) -> ProxyResponse:

        fetched, errors = [], []

        for datasource in self.datasources:
            try:
                fetched.append(await datasource.fetch_data())
            except Exception as exception:  # pylint: disable=broad-except
                logging.getLogger(__name__).exception(exception)

                if include_tracebacks:
                    error_message = traceback.format_exc()
                elif include_exceptions:
                    error_message = str(exception)
                else:
                    error_message = "Error happened!"

                # not the best fix, but at least it works
                if error_message == "" and isinstance(exception, asyncio.TimeoutError):
                    error_message = "Timeout!"

                # TODO: `datasource.url` -> `datasource.name` after caching MR merge.
                errors.append({datasource.url: error_message})

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
