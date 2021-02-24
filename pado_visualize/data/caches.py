from __future__ import annotations
import io
import logging
import os
import warnings
from collections import Mapping
from pathlib import Path
from typing import Dict
from typing import Iterator
from typing import Optional

import diskcache
from flask import send_file, abort
from flask import current_app
from itsdangerous import base64_decode, base64_encode
from pado.images import ImageId
from tqdm import tqdm

# note to use these in other modules they have to be initialized first
from pado_visualize.data.slides import get_svs_thumbnail

# flask and dash unrelated data logger
_logger = logging.getLogger(__name__)


thumbnail_cache: _ThumbnailCache


def __getattr__(name):
    if name in {'thumbnail_cache'}:
        logging.error("you have tried to access the caches before calling initialize_caches")
        raise AttributeError(name)


class _ThumbnailCache(Mapping):
    """cache thumbnails as files on disk"""
    max_size = 200
    suffix = "jpg"
    cache_subfolder = "thumbnails"

    def __init__(self, cache_path: Path):
        p = Path(cache_path).joinpath(self.cache_subfolder).absolute().resolve()
        p.mkdir(exist_ok=True)
        self._path = os.fspath(p)

    def __iter__(self) -> Iterator[ImageId]:
        # note: this is not intended to be iterated in a fast way...
        for _, _, files in os.walk(self._path):
            for file in files:
                stem, _ = os.path.splitext(file)
                yield ImageId.from_str(base64_decode(stem).decode())

    def __len__(self) -> int:
        # note: this is not intended to be iterated in a fast way...
        total = 0
        for _, _, files in os.walk(self._path):
            total += len(files)
        return total

    def __getitem__(self, image_id: ImageId) -> str:
        """return the absolute path to the file stored in this cache"""
        fn = self._to_cache_path(image_id)
        if os.path.isfile(fn):
            return fn
        else:
            KeyError(image_id)

    def __setitem__(self, image_id: ImageId, thumbnail_data: bytes) -> None:
        """create an file at the corresponding path in the cache"""
        fn = self._to_cache_path(image_id)
        os.makedirs(os.path.dirname(fn), mode=0o700, exist_ok=True)
        with open(fn, "wb") as f:
            f.write(thumbnail_data)

    def _to_cache_path(self, image_id: ImageId) -> str:
        """provide a path to uniformly distribute thumbnails across directories"""
        if not isinstance(image_id, ImageId):
            raise TypeError(f"requires image_id of type `ImageId`, got: {type(image_id)}")

        # verbatim copy from pado_visualize.extensions.ImageIdConverter
        image_id_str = image_id.to_str()
        webapp_id_str = base64_encode(image_id_str.encode()).decode()

        image_id_hash = image_id.to_url_hash()
        return os.path.join(
            self._path,  # base path
            image_id_hash[0],  # uniform distribution in subfolders
            image_id_hash[0:2],
            image_id_hash[0:3],
            f"{webapp_id_str}.{self.suffix}"  # filename in webapp id style
        )  # ~ 2400 pictures @ 10_000_000 files


def initialize_caches(cache_path: Path):
    global thumbnail_cache
    thumbnail_cache = _ThumbnailCache(cache_path)


def populate_thumbnail_cache():
    global thumbnail_cache
    from pado_visualize.data.dataset import get_image_map

    im: Dict[ImageId, Optional[Path]] = get_image_map()

    skipped_none = 0
    skipped_nofile = 0
    total = len(im)

    for idx, (image_id, local_path) in tqdm(enumerate(im.items()), desc="thumbnail caching"):

        if local_path is None:
            skipped_none += 1
        elif not local_path.is_file():
            skipped_nofile += 1
        else:
            thumbnail_cache[image_id] = get_svs_thumbnail(local_path, max_size=(200, 200))
            _logger.info(f"thumbnail #{idx} (of {total}) :: {image_id!r} :: ok")

    _logger.info(f"thumbnail skipped {skipped_none} of {total} due to None path")
    _logger.info(f"thumbnail skipped {skipped_nofile} of {total} due to file not reachable")
