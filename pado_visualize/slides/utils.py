from __future__ import annotations

import math
import os
from typing import List
from typing import NamedTuple
from typing import TYPE_CHECKING

from flask import current_app
from fsspec.core import OpenFile

from pado.images import ImageId
from pado.images import Image
from pado.io.files import urlpathlike_to_fsspec
from pado.types import OpenFileLike

if TYPE_CHECKING:
    from pado_visualize.data import DatasetProxy


class ImageIdImagePair(NamedTuple):
    id: ImageId
    image: Image


class PaginatedItems(NamedTuple):
    page: int
    pages: int
    items: List[ImageIdImagePair]


def get_paginated_images(ds: DatasetProxy, page: int, page_size: int) -> PaginatedItems:
    """return paginated Images"""
    idx_start = page * page_size
    idx_end = page * page_size + page_size
    ds_index = ds.index
    ds_images = ds.images
    image_ids = ds_index[idx_start:idx_end]
    return PaginatedItems(
        page=page,
        pages=math.ceil(len(ds_images) / page_size),
        items=[ImageIdImagePair(id=image_id, image=ds_images[image_id]) for image_id in image_ids],
    )


def thumbnail_path(image_id: ImageId, size: int) -> OpenFileLike:
    """return a path to the thumbnail image"""
    pc = urlpathlike_to_fsspec(current_app.config["CACHE_PATH"])
    urlhash = image_id.to_url_hash(full=True)
    path = f"thumbnails/{size:d}/{urlhash[:1]}/{urlhash[:2]}/{urlhash[:3]}/{urlhash}.jpg"
    return OpenFile(path=os.path.join(pc.path, path), fs=pc.fs)
