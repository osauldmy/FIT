from typing import Any, Mapping

import pydantic
import pytest

from apixy.entities.datasource import HTTPDataSource, MongoDBDataSource


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
        ),
    )
    def test_valid_httpdatasource(raw_datasource: Mapping[str, Any]) -> None:
        MongoDBDataSource(**raw_datasource)
