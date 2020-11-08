
import io
from flask import abort, send_file

from pado_visualize.app import app
from pado_visualize.data.dataset import get_image_map
from pado_visualize.data.slides import get_svs_thumbnail, get_svs_thumbnail_filtered


def _image_path_from_image_id(image_id):
    # convert image_id to path; raise error if the path doesn't resolve
    im = get_image_map(abort_if_none=True)
    try:
        p = im[image_id]
    except KeyError:
        return abort(404, "image_id is not in dataset")
    if p is None:
        return abort(404, "image_id references a remote image")
    if not p.is_file():
        return abort(404, "image_id resource is not available to server")
    return p


@app.server.route("/thumbnails/slide_<image_id>.jpg")
def serve_thumbnail_jpg(image_id):
    p = _image_path_from_image_id(image_id)
    data = get_svs_thumbnail(p)

    return send_file(
        io.BytesIO(data),
        mimetype="image/jpeg",
        as_attachment=True,
        attachment_filename=f"slide_{image_id}.jpg",
    )


@app.server.route("/thumbnails/tiling_<image_id>.jpg")
def serve_tiling_jpg(image_id):
    p = _image_path_from_image_id(image_id)
    data = get_svs_thumbnail_filtered(p)

    return send_file(
        io.BytesIO(data),
        mimetype="image/jpeg",
        as_attachment=True,
        attachment_filename=f"tiling_{image_id}.jpg",
    )
