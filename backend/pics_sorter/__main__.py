#!/usr/bin/env python3
import logging
from pathlib import Path

import uvicorn
from pics_sorter.const import AppConfig

from .app import get_app


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('main')


def main():
    app_config = AppConfig()

    log.debug(f'app is ok. directory={app_config.static_dir.absolute()}')
    if not app_config.static_dir.exists():
        log.error(f'"{app_config.static_dir}" does not exist')
        exit(1)

    app = get_app(app_config)
    return app


def uvicorn_main():
    uvicorn.run(
        'pics_sorter.__main__:main',
        factory=True,
        host='::1',
        port=8113,
        reload_dirs=['backend'],
        reload=True,
    )


if __name__ == '__main__':
    uvicorn_main()
