import datetime
import logging
import random
from hashlib import sha1
from pathlib import Path
from typing import Callable

import PIL.Image
from elo import LOSS, rate, WIN
from pics_sorter.models import Image
from pics_sorter.utils import move
from sqlalchemy import func, text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fan_tools.python import chunks

from .const import app_ctx


log = logging.getLogger('controller')
PICS_SUFFIX = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.jpg_large'}
TOP_10_DIR = '0_top10'
OTHER_DIR = '1_other'
HIDDEN_DIR = '6_hidden'
RESTORED_DIR = '5_restored'
GOOD = '1_good'
BAD = '9_bad'
LOWER = '3_lower'
SORT = 'sort'


def image_get_size(image: Path) -> tuple[int, int, str, str]:
    """Get image size and orientation"""
    with PIL.Image.open(image) as img:
        width, height = img.size
        orientation = 'landscape' if width > height else 'portrait'
    sha1_sum = sha1(image.read_bytes()).hexdigest()
    return width, height, orientation, sha1_sum


class PicsController:
    def __init__(self, path: Path, db: Callable[[], AsyncSession]):
        self.session_maker = db
        self.path = path
        all_images = list(self.get_images())
        self.all_images = all_images
        log.info(f'{db=}')
        self.db: AsyncSession = self.session_maker()
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
                    try:
                        width, height, orientation, sha1_hash = image_get_size(self.path / rel_path)
                    except PIL.UnidentifiedImageError:
                        continue

                    q = select(Image).filter_by(sha1_hash=sha1_hash)
                    duplicate_image = (await self.db.exec(q)).first()
                    if duplicate_image:
                        duplicate_exists = (self.path / duplicate_image.path).exists()
                    else:
                        duplicate_exists = False

                    if duplicate_image and not duplicate_exists:
                        log.info(f'Moved image: {duplicate_image.path} => {rel_path}')
                        image = duplicate_image
                        image.path = rel_path
                    elif duplicate_exists:
                        image = Image(
                            path=rel_path,
                            width=width,
                            height=height,
                            orientation=orientation,
                            sha1_hash=sha1_hash,
                        )
                        self.db.add(image)
                        await self.commit()
                        log.info(f'Hide duplicated: {rel_path=} vs {duplicate_image.path=}')
                        await self.hide(rel_path)
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
            await self.commit()
        await self.commit()

    def get_images(self):
        for fpath in self.path.rglob('*'):
            if fpath.is_file() and fpath.suffix.lower() in PICS_SUFFIX:
                yield fpath

    async def image_add_extra_count(self, img_path: str, count=1):
        image = await Image.get_by_path(self.db, img_path)
        if not image:
            raise NotImplementedError
        image.extra_count += count
        await self.commit()

    async def get_images_around_pivot(self, db, pivot, num=2):
        diff = text(f'abs(elo_rating - {pivot.elo_rating})')
        order_by = [diff, Image.shown_times.asc(), Image.elo_rating.desc()]
        if self.same_orientation:
            if self.same_orientation == 1:
                order_by.append(Image.orientation.asc())
            else:
                order_by.append(Image.orientation.desc())
        q = (
            select(Image)
            .filter(Image.extra_count == 0, ~Image.hidden, Image.path != pivot.path)
            .order_by(*order_by)
            .limit(num)
        )
        images = (await db.exec(q)).all()
        return images

    async def get_relative_images(self, num):
        """
        if have extra_count = select 1 image
        and select rest with similar elo score and lowest_count
        """
        async with self.session_maker() as db:
            q = (
                select(Image)
                .filter(Image.extra_count > 0)
                .order_by(Image.extra_count.desc(), Image.shown_times.asc())
                .limit(1)
            )
            pivot = (await db.exec(q)).all()

            if pivot:
                pivot = pivot[0]
            else:
                # select images with lowest shown_times
                order_by = [Image.shown_times.asc(), Image.elo_rating.desc()]
                if self.same_orientation:
                    if self.same_orientation == 1:
                        order_by.append(Image.orientation.asc())
                    else:
                        order_by.append(Image.orientation.desc())
                q = (
                    select(Image)
                    .filter(Image.extra_count == 0, ~Image.hidden)
                    .order_by(*order_by)
                    .limit(1)
                )
                pivot = (await db.exec(q)).all()[0]
            images = await self.get_images_around_pivot(db, pivot)
            images.append(pivot)
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
            if image.path == winner:
                winner_obj = image
            elif image.extra_count == 0:
                loosers.append(image)

            if image.extra_count > 0:
                image.extra_count -= 1
            else:
                image.shown_times += 1
        updates = []
        for looser in loosers:
            updates.append([looser, rate(looser.elo_rating, [(LOSS, winner_obj.elo_rating)])])
        winner_before = winner_obj.elo_rating

        new_rating = rate(winner_obj.elo_rating, [(WIN, looser.elo_rating) for looser in loosers])
        await self.new_elo(winner_obj, new_rating)
        for obj, new_rating in updates:
            await self.new_elo(obj, new_rating)
        log.debug(f'{winner_before} => {winner_obj.elo_rating=}')
        await self.commit()

    async def new_elo(self, img, new_rating):
        img.elo_rating = new_rating
        if img.elo_rating > 1200:
            if not img.path.startswith((TOP_10_DIR, GOOD)):
                await self.move(img, GOOD)
        elif img.elo_rating < 1150:
            if not img.path.startswith(BAD):
                await self.move(img, BAD)
        elif img.elo_rating < 1200:
            if not img.path.startswith(LOWER):
                await self.move(img, LOWER)
        img.updated_at = datetime.datetime.now()

    async def hide(self, path: str):
        """
        TODO: move into 6_hidden directory
        """
        log.debug(f'Hide: {path=} {app_ctx.get()=}')
        if image := (await self.db.exec(select(Image).filter_by(path=path))).first():
            image.hidden = True
            await self.move(image, HIDDEN_DIR)

    async def restore_last(self):
        q = select(Image).filter_by(hidden=True).order_by(Image.updated_at.desc()).limit(1)
        last = (await self.db.exec(q)).first()
        if last:
            log.debug(f'Restore: {last.path}')
            last.hidden = False
            await self.move(last, RESTORED_DIR)

    async def move(self, img: Image, dst: str | Path):
        if isinstance(dst, str):
            dst = self.path / dst
            dst.mkdir(exist_ok=True, parents=True)
        else:
            assert dst.is_relative_to(self.path)
        if (dst / img.path) == self.path / img.path:
            log.debug('Already in target dir')
            return

        old_path = img.path
        new_path = move(self.path / img.path, dst)
        img.path = str(new_path.relative_to(self.path))
        img.updated_at = datetime.datetime.now()
        self.db.add(img)
        await self.commit()
        log.debug(f'Moved: {old_path} => {new_path}')

    async def commit(self):
        await self.db.commit()
        self.db = self.session_maker()

    async def build_top10(self):
        top10_new = await Image.get_top_n_query(self.db, n=15)
        top10_curr = await Image.get_in_dir(self.db, TOP_10_DIR)

        for img in top10_new:
            if img in top10_curr:
                continue
            log.debug(f'Move: {img}')
            await self.move(img, TOP_10_DIR)
        for img in top10_curr:
            if img in top10_new:
                continue
            await self.move(img, OTHER_DIR)
