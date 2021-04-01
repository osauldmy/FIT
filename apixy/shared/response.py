from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


# this could be more complex in the future - i.e. to differentiate between error types
class UseCaseResponseStatus(enum.Enum):
    """Marks whether the action succeeded"""

    SUCCESS = enum.auto()
    ERROR = enum.auto()


@dataclass(frozen=True)
class UseCaseResponse(Generic[T]):
    """The base response class."""

    status: UseCaseResponseStatus
    errors: Optional[list[str]]
    content: T

    @classmethod
    def success(cls, content: T) -> UseCaseResponse[T]:
        """Factory function for creating a success-response."""
        return cls(status=UseCaseResponseStatus.SUCCESS, errors=None, content=content)

    @classmethod
    def error(cls, errors: list[str], content: T) -> UseCaseResponse[T]:
        """Factory function for creating a response with errors."""
        return cls(status=UseCaseResponseStatus.ERROR, errors=errors, content=content)
