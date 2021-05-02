import json
import uuid
from typing import Dict, Final, cast

import pytest
import requests

API_URL: Final[str] = "http://api:8000/api/v1"


class TestProjectCRUD:
    @pytest.fixture
    def project_json(self) -> Dict[str, str]:
        return {
            "name": "New project",
            "slug": str(uuid.uuid4()),
            "merge_strategy": "concatenation",
            "description": "This is a description",
        }

    @pytest.fixture
    def create_project(self, project_json: Dict[str, str]) -> requests.Response:
        return requests.post(f"{API_URL}/projects", json=project_json)

    def test_get_all(self) -> None:
        r = requests.get(f"{API_URL}/projects")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    @pytest.mark.dependency(name="post")
    def test_post(self, create_project: requests.Response) -> None:
        assert create_project.status_code == 201
        assert "Location" in create_project.headers
        r_get = requests.get(f"{API_URL}{create_project.headers['Location']}")
        assert r_get.status_code == 200
        get_json = r_get.json()
        assert "id" in get_json
        get_json.pop("id")
        assert get_json == json.loads(cast(bytes, create_project.request.body))

    @pytest.mark.dependency(depends="post")
    def test_put(self, create_project: requests.Response) -> None:
        link = create_project.headers["Location"]
        new_json = {
            "name": "New project 2",
            "slug": str(uuid.uuid4()),
            "merge_strategy": "concatenation",
            "description": "This is a description but modified",
        }
        r = requests.put(f"{API_URL}{link}", json=new_json)
        assert r.status_code == 204
        r_check = requests.get(f"{API_URL}{link}")
        assert r_check.status_code == 200
        r_check_json = r_check.json()
        assert str(r_check_json.pop("id")) in link
        assert r_check_json == new_json

    @pytest.mark.dependency(depends=["post"])
    def test_delete(self, create_project: requests.Response) -> None:
        link = create_project.headers["Location"]
        r = requests.delete(f"{API_URL}{link}")
        assert r.status_code == 204
        r_check = requests.get(f"{API_URL}{link}")
        assert r_check.status_code == 404
