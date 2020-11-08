
import io
from flask import abort, send_file

from pado_visualize.app import app
from pado_visualize.data.dataset import get_image_map
from pado_visualize.data.slides import get_svs_thumbnail


@app.server.route("/thumbnails/<image_id>.jpg")
def serve_thumbnail_jpg(image_id):
    im = get_image_map(abort_if_none=True)
    try:
        p = im[image_id]
    except KeyError:
        return abort(404, "image_id is not in dataset")
    if p is None:
        return abort(404, "image_id references a remote image")
    if not p.is_file():
        return abort(404, "image_id resource is not available to server")

    data = get_svs_thumbnail(p)

    return send_file(
        io.BytesIO(data),
        mimetype="image/jpeg",
        as_attachment=True,
        attachment_filename=f"{image_id}.jpg",
    )
