from typing import Any, Optional

from pydantic import Field

from .shared import ForbidExtraModel


class ProxyResponse(ForbidExtraModel):
    """
    Unified format of fetched and merged data for user.

    :param result: container with successfully fetched and merged data and its size
    :param errors: optional container with errors
    """

    class Container(ForbidExtraModel):
        """
        Simple container with data and its size.
        """

        size: int = Field(0, ge=0)
        data: Any = Field(..., default_factory=list)

    result: Container
    errors: Optional[Container]
