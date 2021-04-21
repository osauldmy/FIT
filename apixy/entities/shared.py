from jmespath.parser import ParsedResult
from pydantic import BaseConfig, BaseModel, Extra


class ForbidExtraModel(BaseModel):
    """
    A base class to enforce DRY.
    Forbids extra attributes in schema, allows only defined.
    """

    class Config(BaseConfig):
        """pydantic options"""

        extra = Extra.forbid


class JSONPathSerializable(ForbidExtraModel):
    """Adds a jmespath json encoder to the model."""

    class Config(BaseConfig):
        """pydantic config"""

        json_encoders = {ParsedResult: lambda x: x.expression}
