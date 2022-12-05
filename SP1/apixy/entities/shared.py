from typing import Any, Dict, Iterable, Type

from pydantic import BaseConfig, BaseModel, Extra


class ForbidExtraModel(BaseModel):
    """
    A base class to enforce DRY.
    Forbids extra attributes in schema, allows only defined.
    """

    class Config(BaseConfig):
        """pydantic options"""

        extra = Extra.forbid


class SchemaExtraConfig:
    """
    A helper class to allow inheriting form multiple Config classes
    that override the schema_extra classmethod.
    """

    @classmethod
    def schema_extra(cls, schema: Dict[str, Any], model: Type["BaseModel"]) -> None:
        pass


class OmitFieldsConfig(SchemaExtraConfig):
    """
    Adds a omit_fields attribute to the Config class.
    Fields specified there will be omitted in the OpenAPI schema.
    Only optional fields can be omitted.
    """

    omit_fields: Iterable[str]

    @classmethod
    def schema_extra(cls, schema: Dict[str, Any], model: Type["BaseModel"]) -> None:
        super(OmitFieldsConfig, cls).schema_extra(schema, model)
        for field in cls.omit_fields:
            if field in schema["required"]:
                raise ValueError("Cannot omit required fields.")
            schema["properties"].pop(field)
