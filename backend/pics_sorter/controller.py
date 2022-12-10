from pathlib import Path
import random


PICS_SUFFIX = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.jpg_large'}


class PicsController:
    def __init__(self, path: Path):
        self.path = path
        all_images = list(self.get_images())
        random.shuffle(all_images)
        self.iterator = iter(all_images)

    def get_images(self):
        for fpath in self.path.rglob('*'):
            if fpath.is_file() and fpath.suffix.lower() in PICS_SUFFIX:
                yield fpath

    def get_relative_images(self):
        for fpath in self.iterator:
            yield fpath.relative_to(self.path)
