from pydantic import BaseConfig, BaseModel, Extra


class ForbidExtraModel(BaseModel):
    """
    A base class to enforce DRY.
    Forbids extra attributes in schema, allows only defined.
    """

    class Config(BaseConfig):
        """pydantic options"""

        extra = Extra.forbid
