import io
from typing import Optional

from flask import abort, send_file
from pado.dataset import PadoDataset
from pado.ext.visualize.app import app
from PIL import Image
from tifffile import TiffFile, TiffPage, TiffPageSeries

dataset: Optional[PadoDataset] = None


def set_dataset(path):
    """quick and dirty solution to speed up prototyping"""
    # fixme: should use some shared way of providing the cached dataset instance
    #   to the individual worker threads...
    global dataset
    try:
        dataset = PadoDataset(path, mode="r")
    except FileNotFoundError:
        dataset = None


def get_dataset() -> Optional[PadoDataset]:
    global dataset
    return dataset


def extract_thumbnail(filename, buffer):
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

    arr = page.asarray(maxworkers=1)
    Image.fromarray(arr).save(buffer, format="JPEG")


@app.server.route("/thumbnails/<image_id>.jpg")
def serve_thumbnail_jpg(image_id):
    # get the dataset
    ds = get_dataset()
    if not ds:
        return abort(500, "dataset not loaded")

    # retrieve the image resource
    try:
        img_resource = ds.images[image_id]
    except KeyError:
        return abort(404, "image is not local")

    # verify the resource is local
    p = img_resource.local_path
    if not p or not p.is_file():
        return abort(404, "image is not local")

    with io.BytesIO() as buffer:
        extract_thumbnail(p, buffer)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="image/jpeg",
            as_attachment=True,
            attachment_filename=f"{image_id}.jpg",
        )
