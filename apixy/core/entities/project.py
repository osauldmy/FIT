import uuid
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from pydantic.types import UUID4


class Project(BaseModel):
    """The Project entity from our domain model."""

    uuid: UUID4
    slug: str


class ProjectRepository:
    """Interface for the persistence layer operating on Project objects"""

    @abstractmethod
    async def get_by_id(self, project_id: uuid.UUID) -> Project:
        """Get a single Project for a known uuid"""

    @abstractmethod
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Project]:
        """Get a filtered list of Projects"""

    @abstractmethod
    async def save(self, project: Project) -> None:
        """Save an updated Project"""
