from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


# this could be more complex in the future - i.e. to differentiate between error types
class AppResponseStatus(enum.Enum):
    """Marks whether the action succeeded"""

    SUCCESS = enum.auto()
    ERROR = enum.auto()


@dataclass(frozen=True)
class AppResponse(Generic[T]):
    """The base response class."""

    status: AppResponseStatus
    errors: Optional[list[str]]
    content: T

    @classmethod
    def success(cls, content: T) -> AppResponse[T]:
        """Factory function for creating a success-response."""
        return cls(status=AppResponseStatus.SUCCESS, errors=None, content=content)

    @classmethod
    def error(cls, errors: list[str], content: T) -> AppResponse[T]:
        """Factory function for creating a response with errors."""
        return cls(status=AppResponseStatus.ERROR, errors=errors, content=content)
