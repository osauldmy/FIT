from typing import Any, Dict, Final
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from tortoise.exceptions import DoesNotExist

from apixy import app, models

client = TestClient(app.app)

DS_ROUTER_BASE_URI: Final[str] = "/api/v1/datasources/"


@pytest.fixture
def ds_kwargs() -> Dict[str, Any]:
    return dict(id=1, url="https://apixy.com/", type="http", jsonpath="*", timeout=1)


@mock.patch("apixy.models.DataSource.get")
def test_datasource_get(mocked_get: mock.AsyncMock, ds_kwargs: Dict[str, Any]) -> None:
    data = {"method": "GET", "body": {}, "headers": {}}
    mocked_get.return_value = models.DataSource(**ds_kwargs, data=data)
    response = client.get(f"{DS_ROUTER_BASE_URI}1")
    ds_kwargs.update(data)
    assert response.json() == ds_kwargs
    assert response.status_code == 200
    mocked_get.assert_called_once_with(id=1)


@mock.patch("apixy.models.DataSource.get")
def test_datasource_get_404(mocked_get: mock.AsyncMock) -> None:
    mocked_get.side_effect = DoesNotExist()
    response = client.get(f"{DS_ROUTER_BASE_URI}1")
    assert response.status_code == 404
    mocked_get.assert_called_once_with(id=1)


@mock.patch("apixy.api.v1.datasources.DataSourcesDB.get_paginated_datasources")
def test_datasources_get_list_empty(mocked: mock.AsyncMock) -> None:
    mocked.return_value = []
    response = client.get(f"{DS_ROUTER_BASE_URI}")
    assert response.json() == []
    assert response.status_code == 200


@mock.patch("apixy.api.v1.datasources.DataSourcesDB.get_paginated_datasources")
def test_datasources_get_list(
    mocked: mock.AsyncMock, ds_kwargs: Dict[str, Any]
) -> None:
    data_http = {"method": "GET", "body": {}, "headers": {}}
    data_sql = {"query": "SELECT * FROM table;"}
    ds_model_http = models.DataSource(**ds_kwargs, data=data_http)
    ds_kwargs["type"] = "sql"
    ds_model_sql = models.DataSource(**ds_kwargs, data=data_sql)
    mocked.return_value = [ds_model_http, ds_model_sql]
    response = client.get(f"{DS_ROUTER_BASE_URI}")
    json = response.json()
    types = {x["type"] for x in json}
    assert types == {"http", "sql"}
    query = {x.get("query", None) for x in json}
    assert query == {"SELECT * FROM table;", None}
    method = {x.get("method", None) for x in json}
    assert method == {"GET", None}
    assert len(json) == 2
    assert response.status_code == 200
