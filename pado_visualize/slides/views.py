from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint
from flask import abort
from flask import current_app
from flask import make_response
from flask import render_template
from flask import request
from flask import send_file
from fsspec.implementations.cached import CachingFileSystem

from pado.io.files import urlpathlike_to_fs_and_path
from pado.io.files import urlpathlike_to_fsspec
from pado_visualize.data import DatasetState
from pado_visualize.data import dataset
from pado_visualize.extensions import cache
from pado_visualize.slides.utils import get_paginated_images
from pado_visualize.slides.utils import thumbnail_fs_and_path
from pado_visualize.slides.utils import thumbnail_image
from pado_visualize.slides.tasks import slide_make_thumbnail_task
from pado_visualize.utils import int_ge_0
from pado_visualize.utils import int_ge_1
from tiffslide.deepzoom import MinimalComputeAperioDZGenerator



if TYPE_CHECKING:
    from pado.images import ImageId


# view blueprint for slide endpoints
blueprint = Blueprint('slides', __name__)


@blueprint.before_request
@dataset.requires_state(DatasetState.READY, abort, 404, "dataset is not initialized")
def dataset_ready():
    pass


@blueprint.route("/")
def index():
    page = request.args.get("page", 0, type=int_ge_0)
    page_size = request.args.get("page_size", 40, type=int_ge_1)
    allowed_page_sizes = {20, 40, 80, 160, 320}
    if page_size not in allowed_page_sizes:
        abort(403, f"page_size must be one of {allowed_page_sizes!r}")
    page_images = get_paginated_images(dataset, page=page, page_size=page_size)
    return render_template(
        "slides/index.html",
        image_id_pairs=page_images.items,
        page=page_images.page,
        page_size=page_size,
        pages=page_images.pages
    )


@blueprint.route("/thumbnail_<image_id:image_id>_<int:size>.jpg")
# @cache.memoize()
def thumbnail(image_id: ImageId, size: int):
    if size not in {100, 200}:
        return abort(403, "thumbnail size not in {100, 200}")

    fs, path = thumbnail_fs_and_path(image_id, size)
    print(fs, path)
    assert fs.protocol == "file", "we assume local cache for now"    
    try:
        return send_file(
            path,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=request.path.split("/")[-1]
        )
    except FileNotFoundError:
        thumbnail_image(image_id, dataset.images[image_id])
        return send_file(
            path,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=request.path.split("/")[-1]
        )
        # slide_make_thumbnail_task.delay(image_id, size)
        # return abort(404, 'image not available')


# --- viewer endpoints ------------------------------------------------

@blueprint.route("/viewer/<image_id:image_id>/osd")
def viewer_openseadragon(image_id: ImageId):
    return render_template("slides/viewer_openseadragon.html", image_id=image_id)


# --- pyramidal tile server -------------------------------------------

@cache.memoize()
def _slide_get_deep_zoom_from_session(image_id: ImageId) -> MinimalComputeAperioDZGenerator:
    """retrieve the deep zoom generator from the user session"""
    fs, path = urlpathlike_to_fs_and_path(dataset.images[image_id].urlpath)
    cached_fs = CachingFileSystem(
        cache_storage=current_app.config["CACHE_PATH"],
        cache_check=1200,
        expiry_time=604800,
        fs=fs,
    )
    of = cached_fs.open(path, mode='rb')
    return MinimalComputeAperioDZGenerator(of)


@blueprint.route('/viewer/<image_id:image_id>/osd/image.dzi')
def slide_dzi(image_id: ImageId):
    try:
        dz = _slide_get_deep_zoom_from_session(image_id)
    except (KeyError, FileNotFoundError) as err:
        return abort(404, str(err))
    resp = make_response(dz.get_dzi())
    resp.mimetype = 'application/xml'
    return resp


@blueprint.route('/viewer/<image_id:image_id>/osd/image_files/<int:level>/<int:col>_<int:row>.jpeg')
def slide_tile(image_id, level, col, row):
    try:
        dz = _slide_get_deep_zoom_from_session(image_id)
    except (KeyError, FileNotFoundError) as err:
        return abort(404, str(err))
    try:
        tile = dz.get_tile(level, col, row)
    except (KeyError, IndexError):
        # Unknown slug
        return abort(404, "tile not found")
    except ValueError:
        # Invalid level or coordinates
        return abort(403, "requested level invalid")
    except NotImplementedError:
        # Invalid level or coordinates
        return abort(404, "not implemented tile request")

    resp = make_response(tile)
    resp.mimetype = 'image/jpeg'
    return resp
