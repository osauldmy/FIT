from collections.abc import Collection
from typing import Any, Dict, Iterable

import pydantic
import pytest

from apixy.entities.merge_strategy import (
    MERGE_STRATEGY_MAPPING,
    ConcatenationMergeStrategy,
    RecursiveMergeStrategy,
)


@pytest.mark.parametrize("string", ("concatenation", "CONCATENATION", "conCATeNATION"))
def test_merge_strategy_mapping_create_success(string: str) -> None:
    assert MERGE_STRATEGY_MAPPING[string.lower()] == ConcatenationMergeStrategy()


def test_merge_strategy_mapping_create_failure_keyerror() -> None:
    with pytest.raises(KeyError):
        MERGE_STRATEGY_MAPPING["FOO"]


# All these type ignores below suppress mypy warnings,
# as this wrong args passing is intentional to test it.
class TestConcatenationMergeStrategy:
    @staticmethod
    def test_creation_success() -> None:
        ConcatenationMergeStrategy()
        ConcatenationMergeStrategy(**{})  # type: ignore

    @staticmethod
    def test_creation_failure() -> None:
        with pytest.raises(TypeError):
            ConcatenationMergeStrategy({})  # type: ignore

        with pytest.raises(pydantic.ValidationError):
            ConcatenationMergeStrategy(foo=42)  # type: ignore

    @staticmethod
    @pytest.mark.parametrize(
        "inputs,outputs_reference",
        (
            ([], {}),
            (
                [{}, {}, {}],
                {"0": {}, "1": {}, "2": {}},
            ),
            (
                [{"a": "b"}, {"b": "c"}, {"c": "d"}],
                {"0": {"a": "b"}, "1": {"b": "c"}, "2": {"c": "d"}},
            ),
            (
                [[1, 2, 3], None],
                {"0": [1, 2, 3], "1": None},
            ),
        ),
    )
    def test_concatenation_merge_strategy_success(
        inputs: Iterable[Any], outputs_reference: Dict[str, Any]
    ) -> None:
        assert ConcatenationMergeStrategy().apply(inputs) == outputs_reference

    @staticmethod
    @pytest.mark.parametrize(
        "inputs,outputs_reference",
        (),
    )
    def test_concatenation_merge_strategy_failure(
        inputs: Iterable[Any], outputs_reference: Dict[str, Any]
    ) -> None:
        assert ConcatenationMergeStrategy().apply(inputs) == outputs_reference


class TestRecursiveMergeStrategy:
    @staticmethod
    @pytest.mark.parametrize(
        "inputs,outputs",
        (
            # Handling single datasource output
            ((None,), None),
            (([],), []),
            (("foo",), "foo"),
            ((["foo", "bar"],), ["foo", "bar"]),
            # Ignoring Nones
            (([0, 1, 2, 3], None), [0, 1, 2, 3]),
            (([0, 1, 2, 3], None, None), [0, 1, 2, 3]),
            ((None, [0, 1, 2, 3], None), [0, 1, 2, 3]),
            # Reducing duplicates
            ((None, None), None),
            ((["a", "b"], ["a", "b"]), ["a", "b"]),
            (([0, 1], [0, 1]), [0, 1]),
            (
                (
                    {"a": [1, 2, 3], "b": [4, 5, 6]},
                    {"a": [1, 2, 3], "b": [4, 5, 6]},
                ),
                {"a": [1, 2, 3], "b": [4, 5, 6]},
            ),
            # Concatenating lists
            (
                ([0, 1, 2, 3], [4, 5, 6]),
                [0, 1, 2, 3, 4, 5, 6],  # may be different order
            ),
            (
                (["a", "b", "c"], ["d", "e", "f"]),
                ["a", "b", "c", "d", "e", "f"],  # may be different order
            ),
            (("abc", "def"), ["abc", "def"]),
            (("abc", "def", "ghi"), ["abc", "def", "ghi"]),
            # Edge-cases
            (
                (
                    {"a": [1, 2, 3], "b": [4, 5, 6, 7]},
                    {"a": [1, 2, 3], "b": [4, 5, 6]},
                ),
                {"a": [1, 2, 3], "b": [4, 5, 6, 7]},
            ),
            (
                (
                    {"a": [1, 2, 3], "b": [4, 5, 6]},
                    {"a": [1, 2, 3], "b": [4, 5, 6, 7]},
                ),
                {"a": [1, 2, 3], "b": [4, 5, 6, 7]},
            ),
            (
                (
                    {"a": [1, 2, 3, 4], "b": [4, 5, 6]},
                    {"a": [1, 2, 3], "b": [4, 5, 6, 7]},
                ),
                {"a": [1, 2, 3, 4], "b": [4, 5, 6, 7]},
            ),
            (
                (
                    {"a": [1, 2, 3, 4]},
                    {"b": [4, 5, 6, 7]},
                ),
                {"a": [1, 2, 3, 4], "b": [4, 5, 6, 7]},
            ),
            (
                (
                    {"a": [1, 2, 3, 4], "b": [4, 5, 6]},
                    {"c": [1, 2, 3], "d": [4, 5, 6, 7]},
                ),
                {
                    "a": [1, 2, 3, 4],
                    "b": [4, 5, 6],
                    "c": [1, 2, 3],
                    "d": [4, 5, 6, 7],
                },
            ),
            (
                (
                    {"a": [1, 2, 3, 4], "b": [4, 5, 6]},
                    {"b": [1, 2, 3], "c": [4, 5, 6, 7]},
                ),
                {
                    "a": [1, 2, 3, 4],
                    "b": [1, 2, 3, 4, 5, 6],
                    "c": [4, 5, 6, 7],
                },
            ),
            (
                (
                    {"a": [1, 2, 3, 4], "b": [4, 5, 6]},
                    {"b": [4, 5, 6], "c": [4, 5, 6, 7]},
                ),
                {
                    "a": [1, 2, 3, 4],
                    "b": [4, 5, 6],
                    "c": [4, 5, 6, 7],
                },
            ),
            (
                ({"a": "b"}, "foobar"),
                [{"a": "b"}, "foobar"],
            ),
            (
                ({"a": "b"}, [1, 2, 3]),
                [{"a": "b"}, [1, 2, 3]],
            ),
        ),
    )
    def test_simple_merge_success(
        inputs: Iterable[Any], outputs: Collection[Any]
    ) -> None:
        assert RecursiveMergeStrategy().apply(inputs) == outputs
