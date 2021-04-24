from tortoise import fields
from tortoise.models import Model


class Project(Model):
    """The DB entity for Project"""

    # slug is globally unique for now - this might need to be changed in the future
    slug = fields.CharField(128, unique=True)
    name = fields.CharField(64)
    description = fields.CharField(512, null=True)
