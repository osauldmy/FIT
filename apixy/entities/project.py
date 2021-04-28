from typing import List, Optional

from pydantic import Field

from .datasource import DataSourceUnion
from .merge_strategy import MERGE_STRATEGY_MAPPING
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
    datasources: List[DataSourceUnion]


class ProjectInput(Project):
    class Config(OmitFieldsConfig, Project.Config):
        omit_fields = ("id",)
