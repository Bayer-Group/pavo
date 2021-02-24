"""Emulate OpenSlide's Deep Zoom image generator with tifffile"""
import json
import math
import os
from collections import defaultdict
from functools import lru_cache, wraps
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Optional
from typing import Tuple
from typing import Union
from xml.etree.ElementTree import ElementTree, Element, SubElement

import numpy as np
from PIL import Image, ImageFile
from tifffile import TiffFile, TiffPage, TiffPageSeries, TIFF
from palo.tissue_filter import apply_image_filters

ImageFile.LOAD_TRUNCATED_IMAGES = True
PathOrStr = Union[Path, str]


class SlideLevelError(Exception):
    pass


_svs_locks = defaultdict(Lock)


def _per_image_thread_lock(salt=None):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = (salt, args[0])
            with _svs_locks[cache_key]:
                return func(*args, **kwargs)
        return wrapper

    return decorator


@lru_cache(maxsize=16)
@_per_image_thread_lock("image")
def _get_svs_series(filename: PathOrStr, name: str) -> TiffPageSeries:
    """return the requested series from a tifffile"""
    t = TiffFile(filename)

    # get the requested series
    for series in t.series:
        if series.name == name:
            return series
    else:
        raise LookupError(f"no series with name='{name}' in {filename}")


@lru_cache(maxsize=64)
@_per_image_thread_lock("tile")
def get_svs_tile(filename: PathOrStr, level: int, x: int, y: int) -> bytes:
    """dump a single tile from an svs as a jpeg into a buffer"""
    series = _get_svs_series(filename, "Baseline")
    assert series.is_pyramidal

    # try to get correct level, raise IndexError if not
    try:
        page_series = series.levels[level]
    except IndexError:
        raise SlideLevelError(f"requires 0 <= level < {len(series.levels)} got {level}")
    # ensure that current page_series uses only one page
    page: TiffPage
    page, = page_series.pages

    # noinspection PyUnresolvedReferences
    assert (
        page.compression == TIFF.COMPRESSION.JPEG
        and page.is_tiled
        and page.planarconfig == TIFF.PLANARCONFIG.CONTIG
    )

    # calculate indices
    st_length, st_width = page.tilelength, page.tilewidth
    im_length, im_width = page.shaped[2:4]
    idx_width = (im_width + st_width - 1) // st_width
    idx_length = (im_length + st_length - 1) // st_length

    if not ((0 <= x < idx_width) and (0 <= y < idx_length)):
        raise IndexError(f"tile index ({x}, {y}) at level={level} out of bounds: max ({idx_width}, {idx_length})")

    # index for reading tile
    tile_index = y * idx_width + x

    (data, _), = page.parent.filehandle.read_segments(
        [page.dataoffsets[tile_index]],
        [page.databytecounts[tile_index]],
    )

    jpeg_tables_tag, = (tag for tag in page.tags.values() if tag.name == "JPEGTables")

    with BytesIO() as buffer:
        buffer.write(jpeg_tables_tag.value[:-2])
        # See https://stackoverflow.com/questions/8747904/extract-jpeg-from-tiff-file/9658206#9658206
        buffer.write(b"\xFF\xEE\x00\x0E\x41\x64\x6F\x62\x65\x00\x64\x80\x00\x00\x00\x00")  # colorspace fix
        buffer.write(data[2:])
        tile_data = buffer.getvalue()

    # cut output if needed
    out_width = ((im_width - 1) % st_width) + 1 if x == idx_width - 1 else st_width
    out_length = ((im_length - 1) % st_length) + 1 if y == idx_length - 1 else st_length
    if out_width < st_width or out_length < st_length:
        with BytesIO(tile_data) as buffer:
            im = Image.open(buffer).crop((0, 0, out_width, out_length))
        with BytesIO() as buffer:
            im.save(buffer, format="JPEG")
            return buffer.getvalue()

    return tile_data


@lru_cache(maxsize=1)
def get_svs_thumbnail(filename: PathOrStr, *, max_size: Optional[Tuple[int, int]] = None) -> bytes:
    """extract the binary data of a thumbnail from the whole-slide image"""
    series = _get_svs_series(filename, "Thumbnail")
    assert not series.is_pyramidal

    # this series should have only one page
    page: TiffPage
    page, = series.pages

    # get the thumbnail as array
    arr = page.asarray(maxworkers=1)

    with BytesIO() as buffer:
        im = Image.fromarray(arr)
        if max_size:
            im.thumbnail(max_size, Image.ANTIALIAS)
        im.save(buffer, format="JPEG")
        return buffer.getvalue()


@lru_cache(maxsize=1)
def get_svs_thumbnail_filtered(filename: PathOrStr) -> bytes:
    """extract the binary data of a thumbnail from the whole-slide image"""
    thumbnail_series = _get_svs_series(filename, "Thumbnail")
    baseline_series = _get_svs_series(filename, "Thumbnail")
    assert not thumbnail_series.is_pyramidal

    # this series should have only one page
    page: TiffPage
    page, = thumbnail_series.pages

    org_h, org_w, _ = baseline_series.shape
    scale_factor = 32  # fixme: expose
    new_w = math.floor(org_w / scale_factor)
    new_h = math.floor(org_h / scale_factor)

    # get the thumbnail as array
    arr = page.asarray(maxworkers=1)
    im = Image.fromarray(arr).resize((new_w, new_h), Image.BILINEAR)
    np_img = np.array(im)

    # horribly slow...
    # todo: this is no place for a ~500ms conversion...
    filtered_np_img = apply_image_filters(
        np_img, display=False, remove_red_pen=False
    )

    with BytesIO() as buffer:
        im = Image.fromarray(filtered_np_img)
        im.save(buffer, format="JPEG")
        return buffer.getvalue()


class TifffileDeepZoomGenerator:
    """Minimal-compute OpenSlide-free Deep Zoom tile generator"""

    def __init__(self, svs_filename: PathOrStr):
        self._fn = os.fspath(Path(svs_filename).absolute().resolve())

        # Get information from baseline layers
        baseline = _get_svs_series(self._fn, "Baseline")
        assert baseline.keyframe.tilewidth == baseline.keyframe.tilelength
        self._tile_size = baseline.keyframe.tilewidth
        self._im_levels = tuple(lvl.shape[1::-1] for lvl in baseline.levels)

        # generate the levels for deep zoom
        dz_levels = dz_lvl, = [self._im_levels[0]]
        while dz_lvl[0] > 1 or dz_lvl[1] > 1:
            dz_lvl = tuple(max(1, int(math.ceil(z / 2))) for z in dz_lvl)
            dz_levels.append(dz_lvl)
        self._dz_levels = tuple(reversed(dz_levels))

        self._mapped_levels = {}
        for im_idx, im_lvl in enumerate(self._im_levels):
            for dz_idx, dz_lvl in enumerate(self._dz_levels):
                if abs(im_lvl[0] - dz_lvl[0]) <= 1 and abs(im_lvl[1] - dz_lvl[1]) <= 1:
                    self._mapped_levels[dz_idx] = im_idx

    @property
    def level_size(self):
        """return a dictionary of tile index sizes"""
        return {
            idx: tuple(int(math.ceil(z / self._tile_size)) for z in lvl)
            for idx, lvl in enumerate(self._dz_levels)
        }

    def get_tile_pil(self, level, address) -> Image:
        data = self.get_tile(level, address)
        with BytesIO(data) as fp:
            return Image.open(fp)

    def get_tile(self, level, address) -> bytes:
        """return the jpeg tile as bytes"""
        x, y = address

        if level in self._mapped_levels:
            # there's a direct mapping to a svs tiled level
            im_lvl = self._mapped_levels[level]
            return get_svs_tile(self._fn, level=im_lvl, x=x, y=y)

        elif 8 <= level <= max(self._mapped_levels):
            # we need to compute new tiles from lower levels
            dst = Image.new('RGB', (2 * self._tile_size, 2 * self._tile_size))

            out_width = out_height = 0
            for ix, iy in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                address_1 = 2 * x + ix, 2 * y + iy

                try:
                    # the recursive call is only really a problem for the small (low magnification)
                    # deep zoom tile levels, the bigger ones (high magnification) hit after one recursion
                    data = self.get_tile(level + 1, address_1)
                except IndexError:
                    continue

                with BytesIO(data) as buffer:
                    im = Image.open(buffer)
                    if ix == 0:
                        out_height += im.height
                    if iy == 0:
                        out_width += im.width
                    dst.paste(im, (ix * self._tile_size, iy * self._tile_size))

            if out_width == 0 or out_height == 0:
                raise IndexError(f"tile index ({x}, {y}) at INTERMEDIATE level={level} out of bounds")

            elif (out_width, out_height) != dst.size:
                dst = dst.crop((0, 0, out_width, out_height))
                thumb_size = (max(1, out_width // 2), max(1, out_height // 2))

            else:
                thumb_size = (self._tile_size, self._tile_size)

            dst.thumbnail(thumb_size, Image.ANTIALIAS)
            with BytesIO() as buffer:
                dst.save(buffer, format="JPEG")
                return buffer.getvalue()

        else:
            raise SlideLevelError("requested level invalid")

    def get_dzi(self):
        """return the dzi XML metadata"""
        image = Element(
            "Image",
            TileSize=str(self._tile_size),
            Overlap="0",
            Format="jpeg",
            xmlns="http://schemas.microsoft.com/deepzoom/2008"
        )
        width, height = self._im_levels[0]
        SubElement(image, "Size", Width=str(width), Height=str(height))
        tree = ElementTree(element=image)

        with BytesIO() as buffer:
            tree.write(buffer, encoding="UTF-8")
            return buffer.getvalue().decode("UTF-8")

    def serialize(self):
        json_dict = json.dumps((self.__class__.__name__, vars(self)))
        return json_dict

    @classmethod
    def deserialize(cls, serialized):
        cls_name, inst_dict = json.loads(serialized)
        assert cls_name == cls.__name__
        inst_dict['_mapped_levels'] = {int(k): v for k, v in inst_dict['_mapped_levels'].items()}
        inst = cls.__new__(cls)
        inst.__dict__ = inst_dict
        return inst


def _test_tifffile_timing():
    # build some load stats for a slide
    import random
    import sys
    import time
    from contextlib import contextmanager
    from operator import itemgetter

    if len(sys.argv) != 2:
        print("please provide a svs file as a cli argument")
        sys.exit(1)
    else:
        svs_fn = sys.argv[1]

    num_samples = 100

    @contextmanager
    def timer(label: str, samples: int = 1):
        t0 = time.time()
        yield
        avg = (time.time() - t0) / samples
        print(f"{label} took {avg} seconds")

    with timer("create dz"):
        dz = TifffileDeepZoomGenerator(svs_fn)

    for test_lvl, lvl_size in sorted(dz.level_size.items(), key=itemgetter(0), reverse=True):
        if test_lvl < 8:
            print("skipping small levels")
            break

        test_idx = range(lvl_size[0] * lvl_size[1])
        if len(test_idx) > num_samples:
            test_idx = random.sample(test_idx, num_samples)

        with timer(f"accessing level {test_lvl}", samples=len(test_idx)):
            for flat_idx in test_idx:
                addr = flat_idx % lvl_size[0], flat_idx // lvl_size[0]
                dz.get_tile(test_lvl, addr)

    print("done.")


if __name__ == "__main__":
    _test_tifffile_timing()
