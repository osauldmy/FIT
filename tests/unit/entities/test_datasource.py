from typing import Any, Mapping
from unittest import mock

import pydantic
import pytest

from apixy.entities.datasource import HTTPDataSource, MongoDBDataSource
from tests.fixtures import http_mock  # noqa: F401


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
        ),
    )
    def test_invalid_httpdatasource(raw_datasource: Mapping[str, Any]) -> None:
        with pytest.raises(pydantic.ValidationError):
            HTTPDataSource(**raw_datasource)

    @staticmethod
    @pytest.mark.parametrize(
        "raw_datasource",
        (
            {"url": "https://google.com", "method": "GET", "jsonpath": "*"},
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
    async def test_http_datasource_mock_fetch_success(
        http_mock: Any,  # noqa: F811
    ) -> None:

        http_datasource = HTTPDataSource(
            url="http://httpbin.org/get",
            method="GET",
            jsonpath="[*]",
        )

        payload = ["a", "b"]

        http_mock.add(
            url=http_datasource.url,
            method=http_datasource.method,
            status=200,
            payload=payload,
        )

        data = await http_datasource.fetch_data()
        assert data["result"] == payload


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

        assert data["result"] == payload
