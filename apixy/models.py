from __future__ import annotations

from abc import abstractmethod
from typing import Generic, Type, TypeVar

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model

from apixy.entities.datasource import DATA_SOURCES
from apixy.entities.datasource import DataSource as DataSourceEntity
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


class DataSource(ORMModel[DataSourceEntity], Model):
    """The DB entity for DataSource"""

    # todo: add n:n decomposition
    id = fields.IntField(pk=True)
    url = fields.CharField(max_length=1024)
    type = fields.CharField(max_length=32)
    jsonpath = fields.CharField(max_length=128)
    timeout = fields.FloatField(null=True)
    data = fields.JSONField()

    def to_pydantic(self) -> DataSourceEntity:
        """
        :raises KeyError: on wrong datasource name in `type`
        :raises pydantic.ValidationError: on wrong data passed to entity initializer
        """
        datasource_class: Type[DataSourceEntity] = DATA_SOURCES[self.type]
        return datasource_class(
            id=self.id,
            url=self.url,
            jsonpath=self.jsonpath,
            timeout=self.timeout,
            **self.data
        )

    @classmethod
    def from_pydantic(cls, entity: DataSourceEntity) -> DataSource:
        entity_dict = entity.dict(exclude={"id"})
        return cls(
            url=str(entity_dict.pop("url")),
            type=entity.schema()["title"].replace("DataSourceInput", "").lower(),
            jsonpath=entity_dict.pop("jsonpath"),
            timeout=entity_dict.pop("timeout"),
            data=entity_dict,
        )

    def apply_update(self, entity: DataSourceEntity) -> None:
        entity_dict = entity.dict(exclude={"id"})
        self.url = entity_dict.pop("url")
        self.timeout = entity_dict.pop("timeout")
        self.jsonpath = entity_dict.pop("jsonpath")
        self.data.update(entity_dict)


# TODO possibility to make own Dict encoder or decoder for JSONField
