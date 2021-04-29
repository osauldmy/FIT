from typing import Any, List, Mapping
from unittest import mock

import aioresponses
import pydantic
import pytest

from apixy import models
from apixy.entities.datasource import HTTPDataSource, MongoDBDataSource, SQLDataSource
from tests.unit.datasource_json_responses.spacex_rockets import PAYLOAD_SPACEX_ROCKETS


class TestHTTPDataSource:
    @staticmethod
    @pytest.mark.parametrize(
        "raw_datasource",
        (
            dict(),  # invalid1
            {"foo": "bar"},  # invalid2
            {"url": "example.com"},  # missing most of attributes
            {"url": "", "method": "FOO"},  # wrong HTTP method
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "",  # empty jmespath
            },
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
                "a": "b",  # extra attribute
            },
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
                "headers": [""],  # wrong attr type
            },
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
                "body": [""],  # wrong attr type
            },
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
                "timeout": -1,  # constraint failure
            },
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
                "type": "peepo",  # wrong type
            },
        ),
    )
    def test_invalid_httpdatasource(raw_datasource: Mapping[str, Any]) -> None:
        with pytest.raises(pydantic.ValidationError):
            HTTPDataSource(**raw_datasource)

    @staticmethod
    @pytest.mark.parametrize(
        "raw_datasource",
        (
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
            },
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
                "headers": {},
            },
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
                "body": [],  # somehow it works...
                "headers": [],  # somehow it works...
            },
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
                "headers": {"Token": "Foo"},
            },
        ),
    )
    def test_valid_httpdatasource(raw_datasource: Mapping[str, Any]) -> None:
        HTTPDataSource(**raw_datasource)

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "raw_datasource, payload, fetched_payload",
        (
            (
                {
                    "url": "http://httpbin.org/get",
                    "method": "GET",
                    "jsonpath": "[*]",
                },
                ["a", "b"],
                ["a", "b"],
            ),
            (
                {
                    "url": "https://api.spacexdata.com/v4/rockets",
                    "method": "GET",
                    "jsonpath": "[*]",
                },
                PAYLOAD_SPACEX_ROCKETS,
                PAYLOAD_SPACEX_ROCKETS,
            ),
            (
                {
                    "url": "https://api.spacexdata.com/v4/rockets",
                    "method": "GET",
                    "jsonpath": "[*].name",
                },
                PAYLOAD_SPACEX_ROCKETS,
                ["Falcon 1", "Falcon 9", "Falcon Heavy", "Starship"],
            ),
            (
                {
                    "url": "https://api.spacexdata.com/v4/rockets",
                    "method": "GET",
                    "jsonpath": "[*].[name,success_rate_pct]",
                    "headers": {"Token": "Foo"},
                },
                PAYLOAD_SPACEX_ROCKETS,
                [
                    ["Falcon 1", 40],
                    ["Falcon 9", 98],
                    ["Falcon Heavy", 100],
                    ["Starship", 0],
                ],
            ),
        ),
    )
    async def test_http_datasource_mock_fetch_success(
        raw_datasource: Mapping[str, Any],
        payload: List[Any],
        fetched_payload: List[Any],
    ) -> None:
        http_datasource = HTTPDataSource(**raw_datasource)
        with aioresponses.aioresponses() as mock:
            mock.add(
                url=http_datasource.url,
                method=http_datasource.method,
                status=200,
                payload=payload,
            )

            data = await http_datasource.fetch_data()
        assert data == fetched_payload


class TestMongoDBDataSource:
    @staticmethod
    @pytest.mark.parametrize(
        "raw_datasource",
        (
            dict(),  # invalid1
            {"foo": "bar"},  # invalid2
            {
                "url": "https://google.com",
                "method": "GET",
                "jsonpath": "*",
            },  # HTTP, not MongoDB
            {
                "url": "mongodb+srv://cluster-0.foo.mongodb.net/apixy",
                "database": "foo",
                "collection": "bar",
            },
        ),
    )
    def test_invalid_mongodbdatasource(raw_datasource: Mapping[str, Any]) -> None:
        with pytest.raises(pydantic.ValidationError):
            MongoDBDataSource(**raw_datasource)

    @staticmethod
    @pytest.mark.parametrize(
        "raw_datasource",
        (
            {
                "url": "mongodb+srv://cluster-0.foo.mongodb.net/apixy",
                "jsonpath": "*",
                "database": "foo",
                "collection": "bar",
                "query": {},
            },
            {
                "url": "mongodb+srv://cluster-0.foo.mongodb.net/apixy",
                "jsonpath": "*",
                "database": "foo",
                "collection": "bar",
                # empty query is also ok
            },
            {
                "url": "mongodb+srv://cluster-0.foo.mongodb.net/apixy",
                "jsonpath": "*",
                "database": "foo",
                "collection": "bar",
                "query": {"a": "b"},
            },
        ),
    )
    def test_valid_mongodb_datasource(raw_datasource: Mapping[str, Any]) -> None:
        MongoDBDataSource(**raw_datasource)

    @staticmethod
    @pytest.mark.asyncio
    async def test_mongodb_datasource_mock_fetch_success() -> None:
        mongodb_datasource = MongoDBDataSource(
            url="mongodb://some.url",
            database="foo",
            collection="bar",
            jsonpath="[*]",
            query={},
        )
        payload = [{"foo": "bar"}, {"bar": "baz"}]

        with mock.patch(
            "motor.motor_asyncio.AsyncIOMotorCollection.find"
        ) as cursor_mock:
            cursor_mock.return_value.to_list = mock.AsyncMock(return_value=payload)
            cursor_mock.return_value.close = mock.AsyncMock()
            data = await mongodb_datasource.fetch_data()

            cursor_mock.return_value.to_list.assert_awaited_once()
            cursor_mock.return_value.close.assert_awaited_once()

        assert data == payload


class TestDataSourceDBModel:
    @staticmethod
    def test_http_datasource_from_pydantic() -> None:
        entity = HTTPDataSource(
            url="https://apixy.com",
            method="POST",
            body={"some": "body", "once": "told me"},
            headers={"Authorization": "123456"},
            jsonpath="*",
            timeout=10,
        )
        model = models.DataSourceModel.from_pydantic(entity)
        assert model.url == entity.url
        assert model.timeout == entity.timeout
        assert model.jsonpath == entity.jsonpath
        assert model.type == "http"
        assert model.data == {
            "method": entity.method,
            "body": entity.body,
            "headers": entity.headers,
        }

    @staticmethod
    def test_mongo_datasource_from_pydantic() -> None:
        entity = MongoDBDataSource(
            url="mongodb://some.url",
            database="foo",
            collection="bar",
            jsonpath="[*]",
            query={},
        )
        model = models.DataSourceModel.from_pydantic(entity)
        assert model.url == entity.url
        assert model.timeout == entity.timeout
        assert model.jsonpath == entity.jsonpath
        assert model.type == "mongo"
        assert model.data == {
            "database": entity.database,
            "query": entity.query,
            "collection": entity.collection,
        }

    @staticmethod
    def test_sql_datasource_from_pydantic() -> None:
        entity = SQLDataSource(
            url="sqlite://localhost",
            jsonpath="[*]",
            timeout=10,
            query="SELECT * FROM table;",
        )
        model = models.DataSourceModel.from_pydantic(entity)
        assert model.url == entity.url
        assert model.timeout == entity.timeout
        assert model.jsonpath == entity.jsonpath
        assert model.type == "sql"
        assert model.data == {
            "query": entity.query,
        }

    @staticmethod
    def test_apply_update() -> None:
        model = models.DataSourceModel(
            url="https://apixy.com",
            jsonpath="*",
            timeout=10,
            type="http",
            data={
                "method": "PATCH",
                "body": {},
                "headers": {"Authorization": "API-KEY-1234"},
            },
        )
        entity = HTTPDataSource(
            url="https://apixy.cz",
            jsonpath="*",
            timeout=20,
            method="GET",
            body={},
            headers={},
        )
        model.apply_update(entity)
        assert model.url == entity.url
        assert model.timeout == entity.timeout
        assert model.data == {
            "method": "GET",
            "body": {},
            "headers": {},
        }
