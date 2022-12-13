import logging
from typing import AsyncGenerator

import sqlalchemy
import sqlalchemy as db
from pics_sorter.const import AppConfig
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.main import SQLModel


Base = declarative_base(metadata=SQLModel.metadata)

log = logging.getLogger('models')
engine = None
async_session = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


class Image(Base):
    __tablename__ = "images"

    id = db.Column('id', db.Integer, db.Identity(always=True), primary_key=True)
    path = db.Column(db.String(1024), nullable=False, unique=True)
    height = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    orientation = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    shown_times = db.Column(db.Integer, nullable=False, default=0, index=True)
    elo_rating = db.Column(db.Integer, nullable=False, default=1200, index=True)


def get_connection_string(config: AppConfig, is_async=True):
    if is_async:
        return f'sqlite+aiosqlite:///{config.pics_dir}/db.sqlite'
    return f'sqlite:///{config.pics_dir}/db.sqlite'


def setup_engine(config: AppConfig):
    global engine, async_session
    db_url = get_connection_string(config)
    log.info(f'DB path: {db_url}')
    engine = create_async_engine(db_url, query_cache_size=1200)
    async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    return engine
