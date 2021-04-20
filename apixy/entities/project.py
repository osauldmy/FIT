from pydantic import BaseModel
from pydantic.types import UUID4


class Project(BaseModel):
    """The Project entity from our domain model."""

    uuid: UUID4
    slug: str
