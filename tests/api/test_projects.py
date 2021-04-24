from typing import Final
from unittest import mock

from fastapi.testclient import TestClient
from tortoise.exceptions import DoesNotExist

from apixy import app, models
from apixy.config import SETTINGS
from apixy.entities.project import ProjectInput

client = TestClient(app.app)

PROJECT_ROUTER_BASE_URI: Final[str] = "/api/v1/projects/"


@mock.patch("apixy.models.Project.get")
def test_project_get(mocked_get: mock.AsyncMock) -> None:
    result_kwargs = dict(id=1, slug="slug", name="name", description=None)
    mocked_get.return_value = models.Project(**result_kwargs)
    response = client.get(f"{PROJECT_ROUTER_BASE_URI}1")
    assert response.json() == result_kwargs
    assert response.status_code == 200
    mocked_get.assert_called_once_with(id=1)


@mock.patch("apixy.models.Project.get")
def test_project_get_404(mocked_get: mock.AsyncMock) -> None:
    mocked_get.side_effect = DoesNotExist()
    response = client.get(f"{PROJECT_ROUTER_BASE_URI}1")
    assert response.status_code == 404
    mocked_get.assert_called_once_with(id=1)


@mock.patch("apixy.api.v1.projects.ProjectsDB.get_paginated_projects")
def test_project_get_list(mocked: mock.AsyncMock) -> None:
    result_kwargs = dict(id=1, slug="slug", name="name", description=None)
    mocked.return_value = [models.Project(**result_kwargs)]
    response = client.get(f"{PROJECT_ROUTER_BASE_URI}")
    assert response.json() == [result_kwargs]
    assert response.status_code == 200
    mocked.assert_called_once_with(SETTINGS.DEFAULT_PAGINATION_LIMIT, 0)


@mock.patch("apixy.api.v1.projects.ProjectsDB.get_paginated_projects")
def test_project_get_list_pagination(mocked: mock.AsyncMock) -> None:
    result_kwargs = dict(id=1, slug="slug", name="name", description=None)
    mocked.return_value = [models.Project(**result_kwargs)]
    response = client.get(f"{PROJECT_ROUTER_BASE_URI}?offset=10&limit=20")
    assert response.json() == [result_kwargs]
    assert response.status_code == 200
    mocked.assert_called_once_with(20, 10)


@mock.patch("apixy.api.v1.projects.ProjectsDB.get_paginated_projects")
def test_project_get_list_empty(mocked: mock.AsyncMock) -> None:
    mocked.return_value = []
    response = client.get(f"{PROJECT_ROUTER_BASE_URI}")
    assert response.json() == []
    assert response.status_code == 200


@mock.patch("apixy.api.v1.projects.ProjectsDB.save_project")
@mock.patch("apixy.api.v1.projects.ProjectsDB.slug_exists")
def test_project_create(
    slug_exists: mock.AsyncMock, save_project: mock.AsyncMock
) -> None:
    slug_exists.return_value = False
    save_project.return_value = 1
    project_in = ProjectInput(slug="slug", name="name", description="desc")
    response = client.post(f"{PROJECT_ROUTER_BASE_URI}", json=project_in.dict())
    assert response.status_code == 201
    assert response.headers["Location"] == "/projects/1"


@mock.patch("apixy.api.v1.projects.ProjectsDB.save_project")
@mock.patch("apixy.api.v1.projects.ProjectsDB.slug_exists")
def test_project_create_slug_exists(
    slug_exists: mock.AsyncMock, save_project: mock.AsyncMock
) -> None:
    slug_exists.return_value = True
    save_project.return_value = 1
    project_in = ProjectInput(slug="slug", name="name", description="desc")
    response = client.post(f"{PROJECT_ROUTER_BASE_URI}", json=project_in.dict())
    assert response.status_code == 409
    save_project.assert_not_called()


@mock.patch("apixy.api.v1.projects.ProjectsDB.project_for_update")
@mock.patch("apixy.api.v1.projects.ProjectsDB.slug_exists")
def test_project_update(
    slug_exists: mock.AsyncMock, project_qs: mock.MagicMock
) -> None:
    slug_exists.return_value = False
    project_qs.return_value.exists = mock.AsyncMock(return_value=True)
    project_qs.return_value.update = mock.AsyncMock()
    project_in = ProjectInput(slug="slug", name="name", description="desc")
    response = client.put(f"{PROJECT_ROUTER_BASE_URI}1", json=project_in.dict())
    assert response.status_code == 204
    slug_exists.assert_called_once_with("slug", 1)
    project_qs.return_value.exists.assert_called_once_with()
    project_qs.return_value.update.assert_called_once_with(**project_in.dict())


@mock.patch("apixy.api.v1.projects.ProjectsDB.project_for_update")
@mock.patch("apixy.api.v1.projects.ProjectsDB.slug_exists")
def test_project_update_existing_slug(
    slug_exists: mock.AsyncMock, project_qs: mock.MagicMock
) -> None:
    slug_exists.return_value = True
    project_qs.return_value.exists = mock.AsyncMock(return_value=True)
    project_qs.return_value.update = mock.AsyncMock()
    project_in = ProjectInput(slug="slug", name="name", description="desc")
    response = client.put(f"{PROJECT_ROUTER_BASE_URI}1", json=project_in.dict())
    assert response.status_code == 409
    project_qs.return_value.update.assert_not_called()


@mock.patch("apixy.api.v1.projects.ProjectsDB.project_for_update")
@mock.patch("apixy.api.v1.projects.ProjectsDB.slug_exists")
def test_project_update_id_not_exists(
    slug_exists: mock.AsyncMock, project_qs: mock.MagicMock
) -> None:
    slug_exists.return_value = False
    project_qs.return_value.exists = mock.AsyncMock(return_value=False)
    project_qs.return_value.update = mock.AsyncMock()
    project_in = ProjectInput(slug="slug", name="name", description="desc")
    response = client.put(f"{PROJECT_ROUTER_BASE_URI}1", json=project_in.dict())
    assert response.status_code == 404
    project_qs.return_value.update.assert_not_called()


@mock.patch("apixy.api.v1.projects.ProjectsDB.project_for_update")
def test_project_delete(project_qs: mock.MagicMock) -> None:
    project_qs.return_value.exists = mock.AsyncMock(return_value=True)
    project_qs.return_value.delete = mock.AsyncMock()
    response = client.delete(f"{PROJECT_ROUTER_BASE_URI}1")
    assert response.status_code == 204
    project_qs.assert_called_once_with(1)
    project_qs.return_value.exists.assert_called_once_with()
    project_qs.return_value.delete.assert_called_once_with()


@mock.patch("apixy.api.v1.projects.ProjectsDB.project_for_update")
def test_project_delete_404(project_qs: mock.MagicMock) -> None:
    project_qs.return_value.exists = mock.AsyncMock(return_value=False)
    project_qs.return_value.delete = mock.AsyncMock()
    response = client.delete(f"{PROJECT_ROUTER_BASE_URI}1")
    assert response.status_code == 404
    project_qs.assert_called_once_with(1)
    project_qs.return_value.exists.assert_called_once_with()
    project_qs.return_value.delete.assert_not_called()
