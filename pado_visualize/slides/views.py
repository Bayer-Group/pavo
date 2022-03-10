from __future__ import annotations

import re
import uuid
from typing import TYPE_CHECKING

from flask import Blueprint
from flask import abort
from flask import current_app
from flask import jsonify
from flask import make_response
from flask import render_template
from flask import request
from flask import send_file

from pado.annotations import Annotation
from pado.annotations import Annotations
from pado.images.providers import image_cached_percentage
from pado.images.providers import image_is_cached_or_local
from pado.io.files import urlpathlike_to_fsspec
from pado_visualize.data import DatasetState
from pado_visualize.data import dataset
from pado_visualize.extensions import cache
from pado_visualize.metadata.utils import get_all_metadata_attribute_options
from pado_visualize.slides.utils import get_paginated_images
from pado_visualize.slides.utils import thumbnail_fs_and_path
from pado_visualize.slides.utils import thumbnail_image
from pado_visualize.utils import check_numeric_list
from pado_visualize.utils import int_ge_0
from pado_visualize.utils import int_ge_1
from tiffslide.deepzoom import MinimalComputeAperioDZGenerator

if TYPE_CHECKING:
    from pado.images import ImageId
    from pado.predictions.providers import ImagePredictionProvider


# view blueprint for slide endpoints
blueprint = Blueprint('slides', __name__)


@blueprint.before_request
@dataset.requires_state(DatasetState.READY, abort, 404, "dataset is not initialized")
def dataset_ready():
    pass

def _unpack_filter_params(request):
    page = request.args.get("page", 0, type=int_ge_0)
    page_size = request.args.get("page_size", 20, type=int_ge_1)
    allowed_page_sizes = {1, 5, 20, 40, 80, 160, 320}
    if page_size not in allowed_page_sizes:
        abort(403, f"page_size must be one of {allowed_page_sizes!r}")
    filter = {
        'filename': request.args.get('filename', None),
        'metadata_key': request.args.get('metadata_key', None),
        'metadata_values': check_numeric_list(request.args.getlist('metadata_values', None)),
    }

    return page, page_size, filter


@blueprint.route("/")
def index():
    page, page_size, filter = _unpack_filter_params(request)
    page_images = get_paginated_images(
        dataset, 
        page=page, 
        page_size=page_size,
        filter=filter
    )

    return render_template(
        "slides/index.html",
        image_id_pairs=page_images.items,
        page=page_images.page,
        page_size=page_size,
        pages=page_images.pages,
        filter=filter,
        metadata_attributes=get_all_metadata_attribute_options(),
    )

@blueprint.route("/thumbnails", methods=['GET'])
def thumbnails():
    page, page_size, filter = _unpack_filter_params(request)
    page_images = get_paginated_images(
        dataset, 
        page=page, 
        page_size=page_size,
        filter=filter
    )

    return render_template(
        "slides/thumbnails.html",
        image_id_pairs=page_images.items,
        page=page_images.page,
        page_size=page_size,
        pages=page_images.pages,
        filter=filter,
        metadata_attributes=get_all_metadata_attribute_options(),
    )

@blueprint.route("/thumbnail_<image_id:image_id>_<int:size>.jpg")
def thumbnail(image_id: ImageId, size: int):
    if size not in {100, 200}:
        return abort(403, "thumbnail size not in {100, 200}")

    fs, path = thumbnail_fs_and_path(image_id, size)
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


# --- viewer endpoints ------------------------------------------------

@blueprint.route("/viewer/<image_id:image_id>/osd")
def viewer_openseadragon(image_id: ImageId):
    """the landing page for the openseadragon viewer"""
    show_annotations = bool(request.args.get("show_annotations", 1, int))
    show_image_predictions = request.args.getlist("show_image_predictions", int)

    # check if we have annotations
    has_annotations = len(dataset.annotations.get(image_id, [])) > 0

    # get a list of the image_predictions
    image_predictions = []
    for idx, ip in enumerate(dataset.predictions.images.get(image_id, [])):
        name = "-".join(str(v) for v in ip.extra_metadata.values()).replace(" ", "-")
        tooltip = " ".join(f"{k}={v!r}" for k, v in ip.extra_metadata.items())
        image_predictions.append({"idx": idx, "name": name, "tooltip": tooltip})

    # metadata
    metadata = {"name": ['/'.join(image_id.parts)]}
    mdf = dataset.metadata.get(image_id, None)
    if mdf is not None and not mdf.empty:
        for col in mdf:
            metadata[col] = mdf[col].unique().tolist()

    return render_template(
        "slides/viewer_openseadragon.html",
        image_id=image_id,
        has_annotations=has_annotations,
        image_predictions=image_predictions,
        show_annotations=show_annotations,
        show_image_predictions=show_image_predictions,
        metadata=metadata,
    )


@blueprint.route("/viewer/<image_id:image_id>/deckgl")
def viewer_deckgl(image_id: ImageId):
    """the landing page for the deck.gl viewer"""
    return render_template("slides/viewer_deckgl.html", image_id=image_id)


@blueprint.route("/cache/<image_id:image_id>/status")
def cache_status(image_id: ImageId):
    """return a json status message about the current cache state"""
    cache_inactive = current_app.config.get("CACHE_IMAGES_PATH", None) is None
    data = {
        'cache': 'inactive' if cache_inactive else 'active',
    }

    try:
        image = dataset.images[image_id]
    except KeyError:
        return {'status': 404, 'ready': False, 'pct_cached': 0.0, **data}

    if cache_inactive:
        return {'status': 200, 'ready': True, 'pct_cached': 0.0, **data}

    elif image_is_cached_or_local(image):
        return {'status': 200, 'ready': True, 'pct_cached': 100.0, **data}

    else:
        pct_cached = image_cached_percentage(image)
        return {'status': 200, 'ready': False, 'pct_cached': pct_cached, **data}


# --- pyramidal tile server -------------------------------------------

@cache.memoize()
def _slide_get_deep_zoom_from_session(
    image_id: ImageId,
    *,
    image_prediction_idx: int | None = None
) -> MinimalComputeAperioDZGenerator:
    """retrieve the deep zoom generator from the user session"""
    if image_prediction_idx is None:
        urlpath = dataset.images[image_id].urlpath
    else:
        # when image_prediction_idx is provided we get the prediction
        _ipp: ImagePredictionProvider = dataset.predictions.images
        urlpath = _ipp[image_id][image_prediction_idx].image.urlpath

    of = urlpathlike_to_fsspec(urlpath)
    # noinspection PyTypeChecker,PydanticTypeChecker
    dzi = MinimalComputeAperioDZGenerator(of)
    return dzi


@blueprint.route('/viewer/<image_id:image_id>/osd/image.dzi')
def slide_dzi(image_id: ImageId):
    ip_idx = request.args.get("image_prediction_idx", default=None, type=int_ge_0)
    try:
        dz = _slide_get_deep_zoom_from_session(image_id, image_prediction_idx=ip_idx)
    except (KeyError, FileNotFoundError) as err:
        return abort(404, str(err))
    resp = make_response(dz.get_dzi())
    resp.mimetype = 'application/xml'
    return resp


@blueprint.route('/viewer/<image_id:image_id>/osd/image_files/<int:level>/<int:col>_<int:row>.jpeg')
def slide_tile(image_id, level, col, row):
    ip_idx = request.args.get("image_prediction_idx", default=None, type=int_ge_0)
    try:
        dz = _slide_get_deep_zoom_from_session(image_id, image_prediction_idx=ip_idx)
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


# --- annotation viewer -------------------------------------------

@blueprint.route('/viewer/<image_id:image_id>/annotations.geojson')
def serve_geojson_annotations(image_id):
    try:
        annotations: Annotations = dataset.annotations[image_id]
    except KeyError:
        return abort(404, f"No annotations found for {image_id!r}")

    data = [
        {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [list(annotation.geometry.exterior.coords)],
            },
            'properties': {
                'classification': {
                    'name': annotation.classification,
                    'color': list(annotation.color.as_rgb_tuple(alpha=False)),
                },
                'area': annotation.geometry.area,
                'object_type': 'annotation',
            }
        } for annotation in annotations]
    return jsonify({
        "type": "FeatureCollection",
        "features": data
    }), 200


@blueprint.route('/viewer/<image_id:image_id>/annotations.json')
def serve_w3c_annotations(image_id):

    try:
        annotations: Annotations = dataset.annotations[image_id]
    except KeyError:
        return abort(404, f"No annotations found for {image_id!r}")

    w3c_annotations = [w3c_like_annotation(annotation) for annotation in annotations] 
    return jsonify(w3c_annotations), 200


def w3c_like_annotation(annotation: Annotation, prefix="anno"):
    """make a w3c annotation like annotation

    see: https://www.w3.org/TR/annotation-vocab/#annotation

    """

    region = annotation.geometry
    class_name = annotation.classification
    safe_class_name = re.sub('[^A-Za-z0-9]+', '', class_name)

    # remove style information from svg for w3c annotation
    _svg_style_re = re.compile(
        r'(fill|stroke)="#[0-9a-f]{6}" ?'
        r'|fill-rule="evenodd" ?'
        r'|(stroke-width|opacity)="[0-9]*([.][0-9]*)?" ?'
    )

    svg_path = region.svg()
    # strip all style information
    svg_path = _svg_style_re.sub("", svg_path)

    return {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": f"{prefix}-{safe_class_name.replace(' ', '').replace(':', '')}-{uuid.uuid4()}",
        "type": "Annotation",
        "body": [{
            "type": "TextualBody",
            "value": safe_class_name,
            "purpose": "tagging",
        }],
        "motivation": "classifying",
        "creator": None,
        "created": None,
        "target": {
            "selector": {
                "type": "SvgSelector",
                "conformsTo" : "https://www.w3.org/TR/annotation-model/#svg-selector",
                "value": f"<svg>{svg_path}</svg>",
            }
        }
    }
