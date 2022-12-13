import logging
import random
from pathlib import Path

import PIL.Image
from elo import LOSS, rate, WIN
from pics_sorter.models import Image
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fan_tools.python import chunks


log = logging.getLogger('controller')
PICS_SUFFIX = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.jpg_large'}


def image_get_size(image: Path) -> tuple[int, int, str]:
    """Get image size and orientation"""
    with PIL.Image.open(image) as img:
        width, height = img.size
        orientation = 'landscape' if width > height else 'portrait'
    return width, height, orientation


class PicsController:
    def __init__(self, path: Path, db: AsyncSession):
        self.path = path
        all_images = list(self.get_images())
        self.all_images = all_images
        log.info(f'{db=}')
        self.db = db

        random.shuffle(all_images)
        self.iterator = iter(all_images)

    async def setup(self):
        for chunk in chunks(self.all_images, 300):
            for image in chunk:
                rel_path = str(image.relative_to(self.path))
                q = select(Image).filter_by(path=rel_path)
                if (await self.db.exec(q)).first() is None:
                    width, height, orientation = image_get_size(self.path / image)
                    self.db.add(
                        Image(path=rel_path, width=width, height=height, orientation=orientation)
                    )
            await self.db.commit()
        await self.db.commit()

    def get_images(self):
        for fpath in self.path.rglob('*'):
            if fpath.is_file() and fpath.suffix.lower() in PICS_SUFFIX:
                yield fpath

    async def get_relative_images(self, num):
        q = select(Image).order_by(Image.shown_times.asc()).limit(num)
        images = (await self.db.exec(q)).all()
        return images

    async def rate(self, winner: str, loosers: list[str]):
        log.debug(f'{winner=} {loosers=}')
        q = select(Image).filter(Image.path.in_(loosers + [winner]))
        images = (await self.db.exec(q)).all()
        loosers = []
        winner_obj = None
        for image in images:
            image.shown_times += 1
            if image.path == winner:
                winner_obj = image
            else:
                loosers.append(image)
        updates = []
        for looser in loosers:
            updates.append([looser, rate(looser.elo_rating, [(LOSS, winner_obj.elo_rating)])])
        winner_before = winner_obj.elo_rating
        winner_obj.elo_rating = rate(
            winner_obj.elo_rating, [(WIN, looser.elo_rating) for looser in loosers]
        )

        for obj, new_rating in updates:
            obj.elo_rating = new_rating
        log.debug(f'{winner_before} => {winner_obj.elo_rating=}')
        await self.db.commit()
