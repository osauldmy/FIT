from tortoise import fields
from tortoise.models import Model


class Project(Model):
    """The DB entity for Project"""

    uuid = fields.UUIDField()
    slug = fields.CharField(128)
