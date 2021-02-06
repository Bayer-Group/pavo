import io
import warnings

import diskcache
from flask import send_file, abort
from tqdm import tqdm

from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset, get_image_map
from pado_visualize.data.slides import get_svs_thumbnail, get_svs_thumbnail_filtered
from pado_visualize.routes._route_utils import _image_path_from_image_id

_thumbnail_cache = diskcache.Cache(".pado_visualize.thumbnail.cache")


def _build_thumbnail_cache():
    global _thumbnail_cache
    image_ids = list(get_dataset().images)
    im = get_image_map()

    i = 0
    for image_id_str in tqdm(image_ids, desc="thumbnail caching"):
        k0 = f"thumbnail-{image_id_str}"
        k1 = f"tiling-{image_id_str}"
        print(k0)

        p = _image_path_from_image_id(image_id_str, abort_if_none=False)
        if p is None:
            _thumbnail_cache[k0] = None
            _thumbnail_cache[k1] = None
        else:
            i += 1
            try:
                _thumbnail_cache[k0] = get_svs_thumbnail(p)
                _thumbnail_cache[k1] = get_svs_thumbnail_filtered(p)
            except BaseException as err:
                warnings.warn(f"{err!r}")

    print(f"cached {i} thumbnails of {len(im)}")



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
