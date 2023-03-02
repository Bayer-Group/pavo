from __future__ import annotations

import hashlib
import io
import math
import os
from typing import TYPE_CHECKING
from typing import List
from typing import Mapping
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import Tuple

import fsspec
from flask import current_app
from pado.images import Image
from pado.images import ImageId
from pado.io.files import fsopen
from pado.io.files import urlpathlike_to_fs_and_path
from pado.types import UrlpathLike
from PIL import Image as PILImage
from werkzeug.datastructures import ImmutableMultiDict

from pavo.api.utils import get_filtered_image_ids

if TYPE_CHECKING:
    from pavo.data import DatasetProxy


# --- pagination --------------------------------------------------------------


class ImageIdImagePair(NamedTuple):
    id: ImageId
    image: Image


class PaginatedItems(NamedTuple):
    page: int
    pages: int
    items: List[ImageIdImagePair]


def get_paginated_images(
    ds: DatasetProxy, page: int, page_size: int, filter: dict | None = None
) -> PaginatedItems:
    """return filtered and paginated Images"""
    if filter is None:
        filter = {}
    ds_index = get_filtered_image_ids(filter, ds)
    idx_start = page * page_size
    idx_end = page * page_size + page_size
    ds_images = ds.images
    image_ids = ds_index[idx_start:idx_end]
    return PaginatedItems(
        page=page,
        pages=math.ceil(len(ds_index) / page_size),
        items=[
            ImageIdImagePair(id=image_id, image=ds_images[image_id])
            for image_id in image_ids
        ],
    )


# --- thumbnails --------------------------------------------------------------

THUMBNAIL_SIZES = (200, 100, 32)


def thumbnail_fs_and_path(
    image_id: ImageId,
    size: int,
    *,
    sizes: Sequence[int] = THUMBNAIL_SIZES,
    fmt: str = "png",
    base_path: Optional[UrlpathLike] = None,
) -> Tuple[fsspec.AbstractFileSystem, str]:
    """return a filesystem and path to the thumbnail image"""
    fs, cache_path = urlpathlike_to_fs_and_path(
        base_path or current_app.config["CACHE_PATH"]
    )
    #
    urlhash = image_id.to_url_id()
    sizeshash = hashlib.sha256(repr(tuple(sizes)).encode()).hexdigest()[:4]
    path = f"thumbnails/{urlhash[:1]}/{urlhash[:2]}/{urlhash[:3]}/thumb.{urlhash}.{sizeshash}.{size:d}x{size:d}.{fmt}"
    return fs, os.path.join(cache_path, path)


def thumbnail_image(
    image_id: ImageId,
    image: Image,
    *,
    sizes: Sequence[int] = THUMBNAIL_SIZES,
    force: bool = False,
    base_path: Optional[UrlpathLike] = None,
) -> None:
    """thumbnail the image"""
    fs, cache_path = urlpathlike_to_fs_and_path(
        base_path or current_app.config["CACHE_PATH"]
    )
    #
    urlhash = image_id.to_url_id()
    sizeshash = hashlib.sha256(repr(tuple(sizes)).encode()).hexdigest()[:4]

    def mkpth(s: tuple[int, int]) -> str:
        return os.path.join(
            cache_path,
            f"thumbnails/{urlhash[:1]}/{urlhash[:2]}/{urlhash[:3]}/thumb.{urlhash}.{sizeshash}.{s[0]:d}x{s[1]:d}.png",
        )

    _sizes = sorted(zip(sizes, sizes), reverse=True)
    p = mkpth(_sizes[-1])
    if fs.isfile(p) and not force:
        return

    with image:
        base_thumb = image.get_thumbnail(_sizes[0])
    for size in _sizes:
        img = base_thumb.copy()
        img.thumbnail(size)

        square = PILImage.new("RGBA", size, (255, 255, 255, 0))
        square.paste(img, ((size[0] - img.size[0]) // 2, (size[1] - img.size[1]) // 2))

        with io.BytesIO() as f:
            square.save(f, format="png", optimize=True, compress_level=9)
            data = f.getvalue()

        path = mkpth(size)
        parent = os.path.dirname(path)
        if not fs.isdir(parent):
            fs.mkdirs(parent, exist_ok=True)

        try:
            with fsopen(fs, path, mode="wb") as f:
                f.write(data)
        except Exception as err:
            print("error3 error", str(err), repr(err))
            fs.rm_file(path)
            raise


# --- filtering ---------------------------------------------------------------


def formdata_to_filter(formdata: ImmutableMultiDict) -> Mapping[str, str]:
    """converts form data into a filter dictionary"""
    raise NotImplementedError("todo")
