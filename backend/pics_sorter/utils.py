#!/usr/bin/env python3
import logging
from pathlib import Path


log = logging.getLogger("utils")


def gen():
    yield ''
    c = 0
    while True:
        c += 1
        yield f'.{c}'


def move(src: Path, dst_dir: Path):
    for suffix in gen():
        new_name = f'{src.stem}{suffix}{src.suffix}'
        dst_path = Path(dst_dir, new_name)
        if dst_path.exists():
            continue
        break
    log.debug(f'Moving: {src} => {dst_path}')
    src.rename(dst_path)
    return dst_path
