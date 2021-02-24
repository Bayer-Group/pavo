from __future__ import annotations
import io
from typing import TYPE_CHECKING

from flask import Blueprint, send_file
from flask import session
from flask import render_template
from flask import abort
from flask import make_response

from pado_visualize.data.caches import thumbnail_cache
from pado_visualize.data.dataset import get_available_image_set
from pado_visualize.data.dataset import get_image_path
from pado_visualize.data.slides import TifffileDeepZoomGenerator, get_svs_thumbnail

if TYPE_CHECKING:
    from pado.images import ImageId


# view blueprint for slide endpoints
blueprint = Blueprint('slides', __name__, url_prefix='/slides')


@blueprint.route("/")
def slides_overview():
    available_images = get_available_image_set()
    return render_template("slides/index.html", image_ids=sorted(available_images))


@blueprint.route("/thumbnail/<image_id:image_id>_thumbnail.jpg")
def slides_thumbnail_jpg(image_id: ImageId):
    try:
        thumb_path: str = thumbnail_cache[image_id]
    except KeyError:
        if image_id in get_available_image_set():
            # fallback fixme: should do this in a worker...
            try:
                p = get_image_path(image_id)
                thumbnail_cache[image_id] = get_svs_thumbnail(p)
                thumb_path = thumbnail_cache[image_id]
            except (ValueError, FileNotFoundError, AssertionError, KeyError) as err:
                return abort(404, str(err))
        else:
            return abort(404, f"{image_id!r} not in available set")

    return send_file(
        thumb_path,
        mimetype="image/jpeg",
        as_attachment=True,
    )


# --- viewer endpoints ------------------------------------------------

@blueprint.route("/osd/<image_id:image_id>")
def slides_openseadragon_viewer(image_id: ImageId):
    return render_template("slides/openseadragon_viewer.html", image_id=image_id)


# --- pyramidal tile server -------------------------------------------

def _slide_get_deep_zoom_from_session(image_id: ImageId) -> TifffileDeepZoomGenerator:
    """retrieve the deep zoom generator from the user session"""
    try:
        _json_dz = session[image_id.to_str()]
    except KeyError:
        # try to get the image
        _image_path = get_image_path(image_id)
        dz = TifffileDeepZoomGenerator(_image_path)
        session[image_id.to_str()] = dz.serialize()
    else:
        dz = TifffileDeepZoomGenerator.deserialize(_json_dz)
    return dz


@blueprint.route('/osd/<image_id:image_id>/image.dzi')
def slide_dzi(image_id: ImageId):
    try:
        dz = _slide_get_deep_zoom_from_session(image_id)
    except (KeyError, FileNotFoundError) as err:
        return abort(404, str(err))
    resp = make_response(dz.get_dzi())
    resp.mimetype = 'application/xml'
    return resp


@blueprint.route('/osd/<image_id:image_id>/image_files/<int:level>/<int:col>_<int:row>.jpeg')
def slide_tile(image_id, level, col, row):
    try:
        dz = _slide_get_deep_zoom_from_session(image_id)
    except (KeyError, FileNotFoundError) as err:
        return abort(404, str(err))
    try:
        tile = dz.get_tile(level, (col, row))
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
