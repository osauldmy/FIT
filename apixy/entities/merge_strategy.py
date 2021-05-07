from abc import abstractmethod
from collections.abc import Collection
from functools import reduce
from typing import Any, Final, Iterable, Mapping

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
    def apply(data: Iterable[Any]) -> Collection[Any]:
        ...


class ConcatenationMergeStrategy(MergeStrategy):
    """
    Simple merge strategy which concatenates results of Collection enumerating them.
    """

    __root__: str = "concatenation"

    @staticmethod
    def apply(data: Iterable[Any]) -> Collection[Any]:
        return {str(index): each for index, each in enumerate(data)}


class RecursiveMergeStrategy(MergeStrategy):
    __root__: str = "recursive"

    @staticmethod
    def apply(data: Iterable[Any]) -> Collection[Any]:
        def _reduce(left: Any, right: Any) -> Any:

            if left == right:
                return left

            if left is None or right is None:
                return left or right

            if type(left) is type(right):
                if isinstance(left, str):
                    return [left, right]

                if isinstance(left, list):
                    return sorted(
                        set(left)
                        .intersection(right)
                        .union(set(left).symmetric_difference(right))
                    )

                if isinstance(left, dict):
                    if left.keys() == right.keys():
                        for key in left:
                            ret = _reduce(left[key], right[key])
                            right[key] = ret
                        return right

                    if intersection := left.keys() & right.keys():
                        new_dict = {}
                        for key in left.keys() | right.keys():
                            if key in intersection:
                                if left[key] == right[key]:
                                    new_dict[key] = left[key]
                                else:
                                    new_dict[key] = _reduce(left[key], right[key])
                            else:
                                new_dict[key] = left.get(key) or right.get(key)
                        return new_dict

                    left.update(right)
                    return left

            if isinstance(left, list) and isinstance(right, (str, int, float, bool)):
                if right not in left:
                    left.append(right)
                    return left
                return left

            if isinstance(right, list) and isinstance(left, (str, int, float, bool)):
                if left not in right:
                    right.append(left)
                    return right
                return right

            return [left, right]

        return reduce(_reduce, data)


MERGE_STRATEGY_MAPPING: Final[Mapping[str, MergeStrategy]] = {
    "concatenation": ConcatenationMergeStrategy(),
    "recursive": RecursiveMergeStrategy(),
}
