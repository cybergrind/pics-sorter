import logging
from functools import partial
from pathlib import Path

from elo import DRAW, LOSS, rate, WIN
from fastapi import APIRouter, FastAPI, Request, WebSocket, WebSocketDisconnect
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


def get_links(req: Request, images):
    return [
        {
            'link': to_link(req.app.url_path_for, x.path),
            'path': x.path,
            'id': x.id,
            'elo_rating': x.elo_rating,
            'extra_count': x.extra_count,
            'height': x.height,
            'width': x.width,
        }
        for x in images
    ]


@root.get('/')
async def index():
    return FileResponse(app_ctx.get()['app_config'].static_dir / 'index.html')


@root.get('/api/pics/')
async def pics(req: Request, is_random:bool = False):
    controller: PicsController = app_ctx.get()['controller']
    if is_random:
        images = await controller.get_random_images(num=3)
    else:
        images = await controller.get_relative_images(num=3)
    image_links = get_links(req, images)
    return {
        'success': True,
        'images': image_links,
        'same_orientation': controller.same_orientation,
        'settings': controller.settings,
    }


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

    try:
        while True:
            msg = await sock.receive_json()
            event = msg.get('event')
            if event == 'rate':
                await controller.rate(msg['winner'], msg['loosers'])
                await sock.send_json({'event': 'rate_success', 'is_random': msg.get('is_random', False)})
            elif event == 'hide':
                await controller.hide(msg['image'])
                await sock.send_json({'event': 'hide_success', 'is_random': msg.get('is_random', False)})
            elif event == 'toggle_setting':
                settings = controller.settings
                current_value = getattr(settings, msg['name'])
                setattr(settings, msg['name'], not current_value)
                await sock.send_json({'event': 'update_settings', 'settings': settings.dict()})
            elif event == 'toggle_orientation':
                settings = controller.settings
                controller.same_orientation = (controller.same_orientation + 1) % 3
                settings.same_orientation = (settings.same_orientation + 1) % 3
            elif event == 'restore_last':
                await controller.restore_last()
                await sock.send_json({'event': 'restore_success', 'is_random': msg.get('is_random', False)})
            elif event == 'build_top10':
                await controller.build_top10()
            elif event == 'add_extra_count':
                await controller.image_add_extra_count(msg['image'], msg.get('count', 1))
                await sock.send_json({'event': 'add_extra_count_success'})
            elif event == 'touch_restart':
                # touch app.py == __file__
                Path(__file__).touch()
    except WebSocketDisconnect:
        pass


async def close_session(controller: PicsController):
    await controller.db.commit()
    await controller.db.close()


def get_app(app_config: AppConfig) -> FastAPI:
    db = setup_engine(app_config)
    from .models import async_session

    controller = PicsController(app_config.pics_dir, async_session)
    app = FastAPI(on_shutdown=[partial(close_session, controller)], on_startup=[controller.setup])

    app_ctx.set({'dir': app_config.pics_dir, 'controller': controller, 'app_config': app_config})
    app.controller = controller
    app.mount('/static', StaticFiles(directory=app_config.static_dir), name='static')
    app.mount('/pics', StaticFiles(directory=app_config.pics_dir), name=DIR)
    app.include_router(root)
    return app
