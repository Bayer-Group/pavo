import io
import json
import math
import tarfile
from pathlib import Path
from typing import Dict, Optional

import numpy as np
from flask import abort, send_file
from pado.dataset import PadoDataset
from pado.ext.visualize.app import app
from PIL import Image
from tifffile import TiffFile, TiffPage, TiffPageSeries

dataset: Optional[PadoDataset] = None
image_map: Dict[str, int] = {}


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


def get_dataset() -> Optional[PadoDataset]:
    global dataset
    return dataset


def get_image_id_map() -> Dict[str, int]:
    global image_map
    return image_map


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


@app.server.route("/thumbnails/<image_id>.jpg")
def serve_thumbnail_jpg(image_id):
    # get the dataset
    ds = get_dataset()
    img_map = get_image_id_map()
    if not ds:
        return abort(500, "dataset not loaded")

    # retrieve the image resource
    try:
        img_resource = ds.images[img_map[image_id]]
    except KeyError:
        return abort(404, f"image_id '{image_id}' not found")

    # check if remote resource
    p = img_resource.local_path
    if p is None:
        return abort(404, "image is remote")

    # verify the resource is local
    if not p.is_file():
        return abort(404, "image is not accessible locally")

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
