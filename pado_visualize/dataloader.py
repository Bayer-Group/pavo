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
from PIL import Image
from tifffile import TiffFile, TiffPage, TiffPageSeries

from pado_visualize.app import app
from pado_visualize.data.slides import get_svs_thumbnail_filtered

wds_map: Dict[str, Path] = {}


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
        p = image_id_to_image_path(image_id)
    except RuntimeError as err:
        return abort(500, str(err))
    except FileNotFoundError as err:
        return abort(404, str(err))

    data = get_svs_thumbnail_filtered(p)

    return send_file(
        io.BytesIO(data),
        mimetype="image/png",
        as_attachment=True,
        attachment_filename=f"{image_id}.png",
    )
