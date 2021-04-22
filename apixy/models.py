from __future__ import annotations

from tortoise import fields
from tortoise.models import Model

from apixy.entities.project import Project as ProjectEntity


class Project(Model):
    """The DB entity for Project"""

    uuid = fields.UUIDField(pk=True)
    slug = fields.CharField(128)
    name = fields.CharField(64)
    description = fields.CharField(512, null=True)

    def to_pydantic(self) -> ProjectEntity:
        """Creates a pydantic model from the db model."""
        return ProjectEntity(
            uuid=self.uuid,
            slug=self.slug,
            name=self.name,
            description=self.description,
        )

    @classmethod
    def from_pydantic(cls, entity: ProjectEntity) -> Project:
        """Creates the DB model from a pydantic model."""
        return cls(
            uuid=entity.uuid,
            slug=entity.slug,
            name=entity.name,
            description=entity.description,
        )
