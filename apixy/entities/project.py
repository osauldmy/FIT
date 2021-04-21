import uuid as uuid_

from pydantic import BaseModel, Field
from pydantic.types import UUID4


class Project(BaseModel):
    """The Project entity from our domain model."""

    uuid: UUID4 = Field(default_factory=uuid_.uuid4)
    slug: str = Field(max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")
    # the regex matches alphanumeric chars separated with hyphens
    # todo: we might want to do this without a regex


class ProjectIn(BaseModel):
    """Project without uuid, used for creation."""

    slug: str

    def to_project(self) -> Project:
        """Creates a Project."""
        return Project(**self.__dict__)
