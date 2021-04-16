from pydantic import BaseModel


class ForbidExtraModel(BaseModel):
    """
    A base class to enforce DRY.
    Forbids extra attributes in schema, allows only defined.
    """

    class Config:
        """pydantic options"""

        extra = "forbid"
