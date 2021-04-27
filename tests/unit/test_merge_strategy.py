from typing import Any, Dict, List

import pydantic
import pytest

from apixy.entities.merge_strategy import ConcatenationMergeStrategy


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
        ),
    )
    def test_concatenation_merge_strategy(
        inputs: List[Any], outputs_reference: Dict[str, Any]
    ) -> None:
        assert ConcatenationMergeStrategy().apply(inputs) == outputs_reference
