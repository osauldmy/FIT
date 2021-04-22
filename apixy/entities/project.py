from typing import Optional

from pydantic import Field

from .shared import ForbidExtraModel


class ProjectBase(ForbidExtraModel):
    name: str = Field(max_length=64)
    slug: str = Field(max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")
    # the regex matches alphanumeric chars separated with hyphens
    # todo: we might want to do this without a regex
    description: Optional[str] = Field(default=None, max_length=512)

    class Config:
        orm_mode = True


class Project(ProjectBase):
    """The Project entity from our domain model."""

    id: int


class ProjectInput(ProjectBase):
    """Project without id, used for creation."""
