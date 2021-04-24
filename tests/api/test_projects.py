import asyncio
from typing import Final
from unittest import mock

from fastapi.testclient import TestClient

from apixy import app, models

client = TestClient(app.app)

PROJECT_ROUTER_BASE_URI: Final[str] = "/api/v1/projects/"


@mock.patch("apixy.models.Project.get", return_value=asyncio.Future())
def test_project_get(mocked_get: mock.MagicMock) -> None:
    mocked_get.return_value.set_result(
        models.Project(id=1, slug="slug", name="name", description=None)
    )
    response = client.get(f"{PROJECT_ROUTER_BASE_URI}1")
    assert response.status_code == 200
    mocked_get.assert_called_once_with(id=1)
