import logging
from functools import partial
from pathlib import Path

from elo import DRAW, LOSS, rate, WIN
from fastapi import APIRouter, FastAPI, Request, WebSocket
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pics_sorter.const import AppConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .const import app_ctx
from .controller import PicsController
from .models import setup_engine


DIR = 'pics'


root = APIRouter()
log = logging.getLogger(__name__)
for name in ['aiosqlite', 'PIL']:
    logging.getLogger(name).setLevel(logging.INFO)


def to_link(url_for, rel_image):
    return url_for(DIR, path=str(rel_image))


async def get_links(req: Request, num=10):
    controller: PicsController = app_ctx.get()['controller']
    images = await controller.get_relative_images(num)
    return [{'link': to_link(req.url_for, x.path), 'path': x.path} for x in images]


@root.get('/')
async def index():
    return FileResponse(app_ctx.get()['app_config'].static_dir / 'index.html')


@root.get('/api/pics/')
async def pics(req: Request):
    controller: PicsController = app_ctx.get()['controller']
    images = await get_links(req, num=3)
    return {'success': True, 'images': images, 'same_orientation': controller.same_orientation}


@root.get('/html')
async def get_html(req: Request):
    urls = get_links(req)
    links = ''.join(f'<a href="{x}">link</a><br/>' for x in urls)
    return HTMLResponse(f'''<!DOCTYPE html><html><body>{links}</body><html>''')


@root.websocket('/ws')
async def ws(sock: WebSocket):
    await sock.accept()
    await sock.send_json({'type': 'echo'})
    controller: PicsController = app_ctx.get()['controller']

    while True:
        msg = await sock.receive_json()
        event = msg.get('event')
        if event == 'rate':
            await controller.rate(msg['winner'], msg['loosers'])
            await sock.send_json({'event': 'rate_success'})
        elif event == 'hide':
            await controller.hide(msg['image'])
        elif event == 'toggle_orientation':
            controller.same_orientation = (controller.same_orientation + 1) % 3


async def close_session(db: AsyncSession):
    await db.commit()
    await db.close()


def get_app(app_config: AppConfig) -> FastAPI:
    db = setup_engine(app_config)
    from .models import async_session

    session = async_session()
    # session.begin()
    controller = PicsController(app_config.pics_dir, session)
    app = FastAPI(on_shutdown=[partial(close_session, session)], on_startup=[controller.setup])

    app_ctx.set({'dir': app_config.pics_dir, 'controller': controller, 'app_config': app_config})
    app.controller = controller
    app.mount('/static', StaticFiles(directory=app_config.static_dir), name='static')
    app.mount('/pics', StaticFiles(directory=app_config.pics_dir), name=DIR)
    app.include_router(root)
    return app
