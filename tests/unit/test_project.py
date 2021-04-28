from typing import Any, Dict

import pytest
from pydantic.error_wrappers import ValidationError

from apixy.entities.project import Project


@pytest.fixture
def sample_project_data() -> Dict[str, Any]:
    return dict(
        id=1, slug="cool-slug", name="New project", merge_strategy="concatenation"
    )


def test_can_create(sample_project_data: Dict[str, Any]) -> None:
    # making sure i can create an instance - validates the other tests
    Project(**sample_project_data)


def test_spaces_in_slug(sample_project_data: Dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        sample_project_data.update(slug="cool slug")
        Project(**sample_project_data)


def test_slash_in_slug(sample_project_data: Dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        sample_project_data.update(slug="cool/slug")
        Project(**sample_project_data)


def test_empty_slug(sample_project_data: Dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        sample_project_data.update(slug="")
        Project(**sample_project_data)


def test_dashed_slug(sample_project_data: Dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        sample_project_data.update(slug="cool-slug-")
        Project(**sample_project_data)


def test_invalid_merge_strategy(sample_project_data: Dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        sample_project_data.update(merge_strategy="conCATeNATION")
        Project(**sample_project_data)
