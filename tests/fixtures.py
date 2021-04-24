import aioresponses
import pytest


@pytest.fixture(scope="package")
def http_mock() -> aioresponses.aioresponses:
    with aioresponses.aioresponses() as mock:
        yield mock
