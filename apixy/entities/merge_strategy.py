from abc import abstractmethod
from enum import Enum
from typing import Any, Iterable, cast

from apixy.entities.shared import ForbidExtraModel


class MergeStrategy(ForbidExtraModel):
    """
    Base class for merge strategies to have same interface.
    Merge strategy is a definition of how datasource outputs should be processed.

    :param __root__: name of the merge strategy
    """

    __root__: str

    @staticmethod
    @abstractmethod
    def apply(data: Iterable[Any]) -> Iterable[Any]:
        ...


class ConcatenationMergeStrategy(MergeStrategy):
    """
    Simple merge strategy with concatenates results of iterable enumerating them.
    """

    __root__: str = "concatenation"

    @staticmethod
    def apply(data: Iterable[Any]) -> Iterable[Any]:
        return {str(index): each for index, each in enumerate(data)}


class MergeStrategyEnum(Enum):
    CONCATENATION = ConcatenationMergeStrategy
    # ... to be continued

    @staticmethod
    def from_str(value: str) -> MergeStrategy:
        """
        :raises KeyError: on non-existing MergeStrategy string value
        """
        return cast(MergeStrategy, MergeStrategyEnum[value.upper()].value())
