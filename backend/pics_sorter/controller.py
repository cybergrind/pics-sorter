import logging
import random
from hashlib import sha1
from pathlib import Path

import PIL.Image
from elo import LOSS, rate, WIN
from pics_sorter.models import Image
from pics_sorter.utils import move
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fan_tools.python import chunks

from .const import app_ctx


log = logging.getLogger('controller')
PICS_SUFFIX = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.jpg_large'}
HIDDEN_DIR = '6_hidden'


def image_get_size(image: Path) -> tuple[int, int, str, str]:
    """Get image size and orientation"""
    with PIL.Image.open(image) as img:
        width, height = img.size
        orientation = 'landscape' if width > height else 'portrait'
    sha1_sum = sha1(image.read_bytes()).hexdigest()
    return width, height, orientation, sha1_sum


class PicsController:
    def __init__(self, path: Path, db: AsyncSession):
        self.path = path
        all_images = list(self.get_images())
        self.all_images = all_images
        log.info(f'{db=}')
        self.db: AsyncSession = db
        self.hidden_dir = self.path / HIDDEN_DIR
        self.hidden_dir.mkdir(exist_ok=True)
        self.same_orientation = 0

        random.shuffle(all_images)
        self.iterator = iter(all_images)

    async def setup(self):
        for chunk in chunks(self.all_images, 300):
            for image in chunk:
                rel_path = str(image.relative_to(self.path))
                q = select(Image).filter_by(path=rel_path)
                image = (await self.db.exec(q)).first()
                if image is None:
                    width, height, orientation, sha1_hash = image_get_size(self.path / rel_path)

                    q = select(Image).filter_by(sha1_hash=sha1_hash)
                    duplicate_image = (await self.db.exec(q)).first()
                    if not (self.path / duplicate_image.path).exists():
                        log.info(f'Moved image: {duplicate_image.path} => {rel_path}')
                        image = duplicate_image
                        image.path = rel_path
                    else:
                        image = Image(
                            path=rel_path,
                            width=width,
                            height=height,
                            orientation=orientation,
                            sha1_hash=sha1_hash,
                        )
                    self.db.add(image)
                elif not image.sha1_hash:
                    width, height, orientation, sha1_hash = image_get_size(self.path / image.path)
                    image.sha1_hash = sha1_hash
            await self.db.commit()
        await self.db.commit()

    def get_images(self):
        for fpath in self.path.rglob('*'):
            if fpath.is_file() and fpath.suffix.lower() in PICS_SUFFIX:
                yield fpath

    async def get_relative_images(self, num):
        order_by = [Image.shown_times.asc(), Image.elo_rating.asc()]
        if self.same_orientation:
            if self.same_orientation == 1:
                order_by.append(Image.orientation.asc())
            else:
                order_by.append(Image.orientation.desc())

        q = select(Image).filter(~Image.hidden).order_by(*order_by).limit(num)
        images = (await self.db.exec(q)).all()
        return images

    async def get_duplicated_images(self, num):
        q = (
            select(Image.sha1_hash)
            .filter(~Image.hidden)
            .limit(num)
            .group_by(Image.sha1_hash)
            .having(func.count(Image.sha1_hash) > 1)
        )
        bad_hashes = [x[0] for x in (await self.db.exec(q)).all()]
        q = (
            select(Image)
            .filter(~Image.hidden, Image.sha1_hash.in_(bad_hashes))
            .order_by(Image.sha1_hash)
            .limit(num)
        )
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

    async def hide(self, path: str):
        """
        TODO: move into 6_hidden directory
        """
        log.debug(f'Hide: {path=} {app_ctx.get()=}')
        if image := (await self.db.exec(select(Image).filter_by(path=path))).first():
            new_path = move(self.path / image.path, self.hidden_dir)
            image.path = str(new_path.relative_to(self.path))
            image.hidden = True
            await self.db.commit()
