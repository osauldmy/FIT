import uuid as uuid_

import pytest
from pydantic.error_wrappers import ValidationError

from apixy.entities.project import Project


def test_can_create() -> None:
    # making sure i can create an instance - validates the other tests
    Project(uuid=uuid_.uuid4(), slug="cool-slug")


def test_spaces_in_slug() -> None:
    with pytest.raises(ValidationError):
        Project(uuid=uuid_.uuid4(), slug="cool slug")


def test_slash_in_slug() -> None:
    with pytest.raises(ValidationError):
        Project(uuid=uuid_.uuid4(), slug="cool/slug")


def test_empty_slug() -> None:
    with pytest.raises(ValidationError):
        Project(uuid=uuid_.uuid4(), slug="")


def test_dashed_slug() -> None:
    with pytest.raises(ValidationError):
        Project(uuid=uuid_.uuid4(), slug="cool-slug-")
