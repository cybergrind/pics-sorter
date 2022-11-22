from fastapi.testclient import TestClient


def test_01_basic(cli: TestClient):
    resp = cli.get('/')
    resp.raise_for_status()
    data = resp.json()
    assert len(data['images']) == 8
