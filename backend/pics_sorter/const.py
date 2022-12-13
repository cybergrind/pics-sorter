from contextvars import ContextVar
from pathlib import Path

from pydantic import BaseSettings, Field


class AppConfig(BaseSettings):
    static_dir: Path | None = Field('frontend/pics-sorter/build', env='STATIC_DIR')
    pics_dir: Path | None = Field('.', env='PICS_DIR')


app_ctx = ContextVar('app_ctx', default={})
