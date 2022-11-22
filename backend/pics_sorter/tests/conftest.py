from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from pathlib import Path
from pics_sorter.app import get_app


@pytest.fixture
def app(pics_dir):
    yield get_app(pics_dir, pics_dir)


@pytest.fixture
def pics_dir(tmp_path):
    pics: Path = tmp_path / 'pics'
    pics.mkdir()
    for i in range(8):
        (pics / f'pic{i}.jpg').touch()
    yield pics


@pytest.fixture
def cli(app: FastAPI):
    yield TestClient(app)
