from __future__ import annotations

from abc import abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model

from apixy.entities.project import Project as ProjectEntity

Entity = TypeVar("Entity", bound=BaseModel)


class ORMModel(Generic[Entity]):
    @abstractmethod
    def to_pydantic(self) -> Entity:
        """Creates a pydantic model from a tortoise model fetched from db."""

    @classmethod
    @abstractmethod
    def from_pydantic(cls, entity: Entity) -> ORMModel[Entity]:
        """Creates a tortoise model instance from a pydantic model."""


class Project(ORMModel[ProjectEntity], Model):
    """The DB entity for Project"""

    id = fields.IntField(pk=True)
    # slug is globally unique for now - this might need to be changed in the future
    slug = fields.CharField(128, unique=True)
    name = fields.CharField(64)
    description = fields.CharField(512, null=True)

    def to_pydantic(self) -> ProjectEntity:
        return ProjectEntity.from_orm(self)

    @classmethod
    def from_pydantic(cls, entity: ProjectEntity) -> Project:
        return cls(**entity.dict())
