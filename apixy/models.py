from tortoise import fields
from tortoise.models import Model


class Project(Model):
    """The DB entity for Project"""

    slug = fields.CharField(128)
    name = fields.CharField(64)
    description = fields.CharField(512, null=True)
