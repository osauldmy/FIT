from typing import Any, Dict, List, Tuple
from unittest import mock

import pytest
from pydantic.error_wrappers import ValidationError

from apixy.entities.datasource import DATA_SOURCES
from apixy.entities.project import Project, ProjectWithDataSources
from tests.unit.datasource_json_responses.spacex_rockets import PAYLOAD_SPACEX_ROCKETS


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data_sources_with_payloads",
    [
        (
            (
                "http",
                [{"foo": "bar"}, {"bar": "baz"}],
            ),
        ),
        (
            (
                "mongo",
                [{"foo": "bar"}, {"bar": "baz"}],
            ),
        ),
        (
            (
                "sql",
                [{"foo": "bar"}, {"bar": "baz"}],
            ),
        ),
        (
            (
                "http",
                [{"foo": "bar"}, {"bar": "baz"}],
            ),
            (
                "http",
                ["Falcon 1", "Falcon 9", "Falcon Heavy", "Starship"],
            ),
        ),
        (
            (
                "http",
                [{"foo": "bar"}, {"bar": "baz"}],
            ),
            (
                "http",
                [{"foo2": "bar2"}, {"bar2": "baz2"}],
            ),
            (
                "sql",
                [
                    ["Falcon 1", 40],
                    ["Falcon 9", 98],
                    ["Falcon Heavy", 100],
                    ["Starship", 0],
                ],
            ),
        ),
        (
            (
                "http",
                [{"foo": "bar"}, {"bar": "baz"}],
            ),
            (
                "http",
                PAYLOAD_SPACEX_ROCKETS,
            ),
            (
                "sql",
                [{"foo3": "bar3"}, {"bar3": "baz3"}],
            ),
        ),
    ],
)
async def test_project_fetch_data_concatenation(
    data_sources_with_payloads: Tuple[Tuple[str, List[Any]], ...]
) -> None:
    data_sources = []
    fetched_payloads = []

    for data_source_class_name, payload in data_sources_with_payloads:
        data_source_class = DATA_SOURCES[data_source_class_name]

        with mock.patch(
            "apixy.entities.datasource." + data_source_class.schema()["title"],
            spec=data_source_class,
            spec_set=True,
        ) as mock_data_source:
            data_source = mock_data_source.return_value

        data_source.copy.return_value.fetch_data = mock.AsyncMock(return_value=payload)

        fetched_payloads.append(payload)
        data_sources.append(data_source)

    project = ProjectWithDataSources(
        name="TestingDemoName",
        slug="testing-demo-name",
        merge_strategy="concatenation",
        datasources=data_sources,
    )

    fetched_project_data = await project.fetch_data()

    for data_source in data_sources:
        data_source.copy.return_value.fetch_data.assert_awaited_once()

    desired_data = {str(i): p for i, p in enumerate(fetched_payloads)}
    assert desired_data == fetched_project_data.result.data
