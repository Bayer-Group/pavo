import io
import json
import math
import tarfile
import warnings
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import tqdm
from flask import abort, send_file
from pado.dataset import PadoDataset
from pado.ext.visualize.app import app
from PIL import Image
from tifffile import TiffFile, TiffPage, TiffPageSeries

dataset: Optional[PadoDataset] = None
image_map: Dict[str, int] = {}
wds_map: Dict[str, Path] = {}


def set_dataset(path):
    """quick and dirty solution to speed up prototyping"""
    # fixme: should use some shared way of providing the cached dataset instance
    #   to the individual worker threads...
    global dataset
    try:
        dataset = PadoDataset(path, mode="r")
    except FileNotFoundError:
        dataset = None
    else:
        image_map.update(((img.id_str, idx) for idx, img in enumerate(dataset.images)))
    return dataset


def set_dataset_from_store(ds):
    global dataset
    dataset = ds
    image_map.update(((img.id_str, idx) for idx, img in enumerate(dataset.images)))
    return dataset


def get_dataset() -> Optional[PadoDataset]:
    global dataset
    return dataset


def get_image_id_map() -> Dict[str, int]:
    global image_map
    return image_map


def set_wds_dirs(*paths: Path):
    global wds_map
    for wds_dir in paths:
        if not wds_dir.is_dir():
            warnings.warn(f"{wds_dir} not a directory")
            continue

        for wds_tar in tqdm.tqdm(wds_dir.glob("*.tar")):
            if wds_tar.with_suffix(wds_tar.suffix + ".error").is_file():
                warnings.warn(f"{wds_tar} ignored due to error")
                continue

            with tarfile.open(wds_tar, mode="r") as tar:
                for tarinfo in tar:
                    if not tarinfo.name.endswith(".json"):
                        continue
                    tile_dict = json.load(tar.extractfile(tarinfo))
                    image_id = tile_dict["IMAGE"]
                    break
                else:
                    image_id = None

            if image_id:
                wds_map[image_id] = wds_tar
    return wds_map


def get_wds_map() -> Dict[str, Path]:
    global wds_map
    return wds_map


def set_wds_map_from_store(x):
    global wds_map
    wds_map = x
    return wds_map


def extract_thumbnail_array(filename):
    """extract the binary data of a thumbnail from the whole-slide image"""
    t = TiffFile(filename)

    # get thumbnail series
    for series in t.series:
        series: TiffPageSeries
        if series.name == "Thumbnail":
            break
    else:
        raise LookupError("no thumbnail in tifffile")

    # this series should have only one page
    page: TiffPage
    (page,) = series.pages

    return page.asarray(maxworkers=1)


def image_id_to_image_path(image_id):
    # get the dataset
    ds = get_dataset()
    img_map = get_image_id_map()
    if not ds:
        raise RuntimeError("dataset not loaded")

    # retrieve the image resource
    try:
        img_resource = ds.images[img_map[image_id]]
    except KeyError:
        raise FileNotFoundError(f"image_id '{image_id}' not found")

    # check if remote resource
    p = img_resource.local_path
    if p is None:
        raise FileNotFoundError("image is remote")

    # verify the resource is local
    if not p.is_file():
        raise FileNotFoundError("image is not accessible locally")

    return p


@app.server.route("/thumbnails/<image_id>.jpg")
def serve_thumbnail_jpg(image_id):
    try:
        p = image_id_to_image_path(image_id)
    except RuntimeError as err:
        return abort(500, str(err))
    except FileNotFoundError as err:
        return abort(404, str(err))

    arr = extract_thumbnail_array(p)

    # save as image
    with io.BytesIO() as buffer:
        Image.fromarray(arr).save(buffer, format="JPEG")
        data = buffer.getvalue()

    return send_file(
        io.BytesIO(data),
        mimetype="image/jpeg",
        as_attachment=True,
        attachment_filename=f"{image_id}.jpg",
    )


def wds_grid_thumbnail_array(wds_tar_path: Path):

    arr = None

    with tarfile.open(wds_tar_path, mode="r") as tar:
        extractfile = tar.extractfile
        json_load = json.load
        for tarinfo in tar:
            if not tarinfo.name.endswith(".json"):
                continue

            tile_dict = json_load(extractfile(tarinfo))
            tile = tile_dict["tile"]
            filt = tile_dict["filter"]
            x, y = tile["slide_x"], tile["slide_y"]
            tw, th = tuple(tile["size"])
            ix, iy = x // tw, y // th

            try:
                arr[iy, ix] = filt["tissue_perc"]
            except TypeError:
                sw, sh = tw + x + filt["dist_right"], th + y + filt["dist_bottom"]
                aw = int(math.ceil(sw / tw))
                ah = int(math.ceil(sh / th))
                arr = np.zeros((ah, aw), dtype=np.float)
                arr[iy, ix] = filt["tissue_perc"]

    # make green channel
    out = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
    out[:, :, 1] = 255
    out[:, :, 3] = 255.0 * arr

    return out


def image_id_to_wds_path(image_id):
    wmap = get_wds_map()

    try:
        wds_path = wmap[image_id]
    except KeyError:
        raise FileNotFoundError(f"no wds key {image_id}")
    return wds_path


@app.server.route("/grid/<image_id>.png")
def serve_grid_png(image_id):
    try:
        p = image_id_to_wds_path(image_id)
    except FileNotFoundError as err:
        return abort(404, str(err))

    arr = wds_grid_thumbnail_array(p)

    with io.BytesIO() as buffer:
        Image.fromarray(arr).save(buffer, format="PNG")
        data = buffer.getvalue()

    return send_file(
        io.BytesIO(data),
        mimetype="image/png",
        as_attachment=True,
        attachment_filename=f"{image_id}.png",
    )
