from abc import abstractmethod
from typing import Generic, TypeVar

from .response import AppResponse

E = TypeVar("E")


class Usecase(Generic[E]):
    """Interface wrapping an action. To be called by an API, a CLI tool etc."""

    @abstractmethod
    async def execute(self) -> AppResponse[E]:
        """Executes the usecase."""
