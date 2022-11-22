import logging
from contextvars import ContextVar
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .controller import PicsController


app_ctx = ContextVar('app_ctx', default={})
DIR = 'pics'


root = APIRouter()
log = logging.getLogger(__name__)


def to_link(url_for, rel_image):
    return url_for(DIR, path=str(rel_image))


def get_links(req: Request, num=10):
    controller: PicsController = app_ctx.get()['controller']
    images = [x for _, x in zip(range(num), controller.get_relative_images())]
    return [to_link(req.url_for, x) for x in images]


@root.get('/')
async def index(req: Request):
    return {'success': True, 'images': get_links(req)}


@root.get('/html')
async def get_html(req: Request):
    urls = get_links(req)
    links = ''.join(f'<a href="{x}">link</a><br/>' for x in urls)
    return HTMLResponse(f'''<!DOCTYPE html><html><body>{links}</body><html>''')


def get_app(static_dir: Path, pics_dir: Path) -> FastAPI:
    app = FastAPI()
    app_ctx.set({'dir': pics_dir, 'controller': PicsController(pics_dir)})
    app.mount('/static', StaticFiles(directory=static_dir), name='static')
    app.mount('/pics', StaticFiles(directory=pics_dir), name=DIR)
    app.include_router(root)
    return app
