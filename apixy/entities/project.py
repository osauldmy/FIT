from typing import Optional

from pydantic import Field

from .shared import ForbidExtraModel, OmitFieldsConfig


class Project(ForbidExtraModel):
    id: Optional[int]
    name: str = Field(max_length=64)
    slug: str = Field(max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")
    # the regex matches alphanumeric chars separated with hyphens
    # todo: we might want to do this without a regex
    description: Optional[str] = Field(default=None, max_length=512)

    class Config:
        orm_mode = True


class ProjectInput(Project):
    class Config(OmitFieldsConfig, Project.Config):
        omit_fields = ("id",)
