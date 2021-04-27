from typing import Any, List, Optional, Union

from pydantic import Field, validator

from .datasource import DataSourceUnion
from .merge_strategy import MergeStrategy, MergeStrategyEnum
from .shared import ForbidExtraModel, OmitFieldsConfig


class Project(ForbidExtraModel):
    id: Optional[int]
    name: str = Field(max_length=64)
    slug: str = Field(max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")
    merge_strategy: Union[str, MergeStrategy]
    # the regex matches alphanumeric chars separated with hyphens
    # todo: we might want to do this without a regex
    description: Optional[str] = Field(default=None, max_length=512)

    class Config:
        orm_mode = True

    @validator("merge_strategy")
    @classmethod
    def validate_merge_strategy(cls, value: Any) -> MergeStrategy:

        if isinstance(value, MergeStrategy):
            return value

        try:
            if isinstance(value, str):
                return MergeStrategyEnum.from_str(value)
        except KeyError as error:
            raise ValueError("Bad MergeStrategy string!") from error

        raise ValueError(
            "merge_strategy should be either a str or a MergeStrategy instance"
        )


class ProjectWithDataSources(Project):
    datasources: List[DataSourceUnion]


class ProjectInput(Project):
    class Config(OmitFieldsConfig, Project.Config):
        omit_fields = ("id",)
