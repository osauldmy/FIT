import requests

url = "http://api:8000/api/v1/"


def test_call() -> None:
    r = requests.get(url + "projects")
    assert r.status_code == 200
