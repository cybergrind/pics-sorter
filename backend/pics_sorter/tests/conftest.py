from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pics_sorter.app import get_app
from pics_sorter.const import AppConfig
from pics_sorter.controller import PicsController
from pics_sorter.models import get_connection_string, setup_engine
from sqlmodel import SQLModel, create_engine


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


@pytest.fixture
def app_config(pics_dir):
    yield AppConfig(static_dir=pics_dir, pics_dir=pics_dir)


@pytest.fixture
def migrated_db(app_config, sync_engine):
    metadata = SQLModel.metadata
    metadata.create_all(sync_engine)


@pytest.fixture
def sync_engine(app_config):
    conn_string = get_connection_string(app_config, is_async=False)
    yield create_engine(conn_string)


@pytest.fixture
def async_engine(app_config, migrated_db):
    engine = setup_engine(app_config)
    yield engine


@pytest.fixture
def async_session(async_engine):
    from pics_sorter.models import async_session

    yield async_session


@pytest.fixture
def controller(app_config, async_session):
    yield PicsController(app_config.pics_dir, async_session)
