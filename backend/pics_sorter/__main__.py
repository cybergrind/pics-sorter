#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

import uvicorn

from .app import get_app


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('main')


def parse_args():
    parser = argparse.ArgumentParser(description='DESCRIPTION')
    parser.add_argument('directory', type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    log.debug('app is ok')
    if not args.directory.exists():
        log.error(f'"{args.directory}" does not exist')
        exit(1)

    app = get_app('frontend/build', args.directory)
    uvicorn.run(app, host='0.0.0.0', port=8006)


if __name__ == '__main__':
    main()
