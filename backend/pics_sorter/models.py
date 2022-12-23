import datetime
import logging
from typing import AsyncGenerator

import sqlalchemy
import sqlalchemy as db
from pics_sorter.const import AppConfig
from sqlalchemy import func
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlmodel import select
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
    __table_args__ = {"sqlite_autoincrement": True}

    id = db.Column('id', db.Integer, autoincrement=True, primary_key=True)
    path = db.Column(db.String(1024), nullable=False, unique=True)
    height = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    orientation = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        server_onupdate=db.func.now(),
        onupdate=datetime.datetime.now(),
    )
    shown_times = db.Column(db.Integer, nullable=False, default=0, index=True)
    elo_rating = db.Column(db.Integer, nullable=False, default=1200, index=True)
    hidden = db.Column(db.Boolean, nullable=False, default=False, index=True)
    sha1_hash = db.Column(db.String(40), nullable=True, index=True)

    @classmethod
    async def get_top_n_query(cls, session: AsyncSession, n=10):
        count = (await session.exec(select(func.count(Image.id)).where(~Image.hidden))).all()[0]
        log.debug(f'{count=}')
        return (
            await session.exec(
                select(Image)
                .where(~Image.hidden)
                .order_by(Image.elo_rating.desc())
                .limit(int(count / 10))
            )
        ).all()

    @classmethod
    async def get_in_dir(cls, session: AsyncSession, path: str):
        return (await session.exec(select(Image).where(Image.path.startswith(path)))).all()


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
