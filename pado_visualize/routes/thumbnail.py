import io
from flask import send_file

from pado_visualize.app import app
from pado_visualize.data.slides import get_svs_thumbnail, get_svs_thumbnail_filtered
from pado_visualize.routes._route_utils import _image_path_from_image_id


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
