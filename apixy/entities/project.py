import uuid as uuid_
from typing import Optional

from pydantic import Field
from pydantic.types import UUID4

from .shared import ForbidExtraModel


class ProjectBase(ForbidExtraModel):
    name: str = Field(max_length=64)
    description: Optional[str] = Field(default=None, max_length=512)
    slug: str = Field(max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")
    # the regex matches alphanumeric chars separated with hyphens
    # todo: we might want to do this without a regex


class Project(ProjectBase):
    """The Project entity from our domain model."""

    uuid: UUID4 = Field(default_factory=uuid_.uuid4)


class ProjectIn(ProjectBase):
    """Project without uuid, used for creation."""

    def to_project(self) -> Project:
        """Creates a Project."""
        return Project(**self.__dict__)
