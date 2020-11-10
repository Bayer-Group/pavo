import io
import shelve

from flask import send_file, abort
from tqdm import tqdm

from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset
from pado_visualize.data.slides import get_svs_thumbnail, get_svs_thumbnail_filtered
from pado_visualize.routes._route_utils import _image_path_from_image_id

_thumbnail_cache = shelve.open(".pado_thumbnail.shelve")


def _build_thumbnail_cache():
    global _thumbnail_cache
    image_ids = get_dataset().images.ids()

    i = 0
    for image_id in tqdm(image_ids, desc="thumbnail caching"):
        k0 = f"thumbnail-{image_id}"
        k1 = f"tiling-{image_id}"

        image_id_str = "__".join(image_id)
        p = _image_path_from_image_id(image_id_str, abort_if_none=False)
        if p is None:
            _thumbnail_cache[k0] = None
            _thumbnail_cache[k1] = None
        else:
            i += 1
            _thumbnail_cache[k0] = get_svs_thumbnail(p)
            _thumbnail_cache[k1] = get_svs_thumbnail_filtered(p)
    print(f"cached {i} thumbnails")


@app.server.route("/thumbnails/slide_<image_id>.jpg")
def serve_thumbnail_jpg(image_id):
    try:
        data = _thumbnail_cache[f"thumbnail-{image_id}"]
    except KeyError:
        # fallback
        p = _image_path_from_image_id(image_id)
        data = get_svs_thumbnail(p)

    if data is None:
        return abort(404, "thumbnail not available")

    return send_file(
        io.BytesIO(data),
        mimetype="image/jpeg",
        as_attachment=True,
        attachment_filename=f"slide_{image_id}.jpg",
    )


@app.server.route("/thumbnails/tiling_<image_id>.jpg")
def serve_tiling_jpg(image_id):
    try:
        data = _thumbnail_cache[f"tiling-{image_id}"]
    except KeyError:
        # fallback
        p = _image_path_from_image_id(image_id)
        data = get_svs_thumbnail_filtered(p)

    if data is None:
        return abort(404, "thumbnail not available")

    return send_file(
        io.BytesIO(data),
        mimetype="image/jpeg",
        as_attachment=True,
        attachment_filename=f"tiling_{image_id}.jpg",
    )
