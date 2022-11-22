from pathlib import Path


PICS_SUFFIX = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.jpg_large'}


class PicsController:
    def __init__(self, path: Path):
        self.path = path

    def get_images(self):
        for fpath in self.path.rglob('*'):
            if fpath.is_file() and fpath.suffix.lower() in PICS_SUFFIX:
                yield fpath

    def get_relative_images(self):
        for fpath in self.get_images():
            yield fpath.relative_to(self.path)
