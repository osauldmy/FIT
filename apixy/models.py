from __future__ import annotations

from abc import abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model

from apixy.entities.datasource import DataSource as DataSourceEntityBase
from apixy.entities.datasource import HTTPDataSource as HTTPDataSourceEntity
from apixy.entities.datasource import MongoDBDataSource as MongoDBDataSourceEntity
from apixy.entities.datasource import SQLDataSource as SQLDataSourceEntity
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


class DataSource(Model):

    url = fields.CharField(max_length=255)
    jsonpath = fields.CharField(max_length=255)
    timeout = fields.FloatField(default=0.0)


class HTTPDataSource(ORMModel[DataSourceEntityBase, HTTPDataSourceEntity], DataSource):

    method = fields.CharField(31)
    body = fields.JSONField()
    headers = fields.JSONField()

    class Meta:
        table = "HTTPDataSource"

    def to_pydantic(self) -> HTTPDataSourceEntity:
        return HTTPDataSourceEntity.from_orm(self)

    @classmethod
    def from_pydantic(cls, entity: DataSourceEntityBase) -> HTTPDataSource:
        return cls(**entity.dict())


class MongoDBDataSource(
    ORMModel[DataSourceEntityBase, MongoDBDataSourceEntity], DataSource
):
    database = fields.CharField(63)
    collection = fields.CharField(63)
    query = fields.JSONField()

    class Meta:
        table = "MongoDBDataSource"

    def to_pydantic(self) -> MongoDBDataSourceEntity:
        return MongoDBDataSourceEntity.from_orm(self)

    @classmethod
    def from_pydantic(cls, entity: DataSourceEntityBase) -> MongoDBDataSource:
        return cls(**entity.dict())


class SQLDataSource(ORMModel[DataSourceEntityBase, SQLDataSourceEntity], DataSource):
    query = fields.TextField()

    class Meta:
        table = "SQLDataSource"

    def to_pydantic(self) -> SQLDataSourceEntity:
        return SQLDataSourceEntity.from_orm(self)

    @classmethod
    def from_pydantic(cls, entity: DataSourceEntityBase) -> SQLDataSource:
        return cls(**entity.dict())


# TODO possibility to make own Dict encoder or decoder for JSONField
