from __future__ import annotations

from abc import abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model

from apixy.entities.project import Project as ProjectEntity
from apixy.entities.project import ProjectBase as ProjectEntityBase

EntityBase = TypeVar("EntityBase", bound=BaseModel)
Entity = TypeVar("Entity", bound=BaseModel)


class ORMModel(Generic[EntityBase, Entity]):
    @abstractmethod
    def to_pydantic(self) -> Entity:
        """Creates a pydantic model from a tortoise model fetched from db."""

    @classmethod
    @abstractmethod
    def from_pydantic(cls, entity: EntityBase) -> ORMModel[EntityBase, Entity]:
        """Creates a tortoise model instance from a pydantic model."""


class Project(ORMModel[ProjectEntityBase, ProjectEntity], Model):
    """The DB entity for Project"""

    id = fields.IntField(pk=True)
    # slug is globally unique for now - this might need to be changed in the future
    slug = fields.CharField(128, unique=True)
    name = fields.CharField(64)
    description = fields.CharField(512, null=True)

    def to_pydantic(self) -> ProjectEntity:
        return ProjectEntity.from_orm(self)

    @classmethod
    def from_pydantic(cls, entity: ProjectEntityBase) -> Project:
        return cls(**entity.dict())
