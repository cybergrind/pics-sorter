#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

from PIL import Image, ImageDraw

from fan_tools.python import rel_path


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('generate_pics')
logging.getLogger('PIL').setLevel(logging.INFO)


def generate_image(path: Path, text: str):
    img = Image.new('RGB', (100, 100), color='red')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill='black')
    img.save(path)


def gen_in_dir(path: Path):
    path.mkdir(exist_ok=True)

    for i in range(10):
        pic = path / f'img_{i}.png'
        generate_image(pic, f'{path.name}_{i}')


def main():
    base = rel_path('../test_pics')
    base.mkdir(exist_ok=True)
    for x in ['0_picked', '1_good', '2_bad']:
        gen_in_dir(base/x)


if __name__ == '__main__':
    main()
