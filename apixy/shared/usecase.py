from abc import abstractmethod
from typing import Generic, TypeVar

from .response import UseCaseResponse

T = TypeVar("T")
E = TypeVar("E")


class Usecase(Generic[T, E]):
    """Interface wrapping an action. To be called by an API, a CLI tool etc."""

    @abstractmethod
    async def execute(self, data: T) -> UseCaseResponse[E]:
        """Executes the usecase."""
