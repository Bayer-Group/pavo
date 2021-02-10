from __future__ import annotations

import re
import uuid
from typing import List
from typing import TYPE_CHECKING
from urllib.parse import unquote

from flask import jsonify, abort

from pado.annotations import Annotation
from pado.images import ImageId
from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset

if TYPE_CHECKING:
    from shapely.geometry.base import BaseGeometry


# remove style information from svg for w3c annotation
_svg_style_re = re.compile(
    r'(fill|stroke)="#[0-9a-f]{6}" ?'
    r'|fill-rule="evenodd" ?'
    r'|(stroke-width|opacity)="[0-9]*([.][0-9]*)?" ?'
)


def w3c_like_annotation(class_name: str, region: BaseGeometry):
    """make a w3c annotation like annotation

    see: https://www.w3.org/TR/annotation-vocab/#annotation

    """
    svg_path = region.svg()
    # strip all style information
    svg_path = _svg_style_re.sub("", svg_path)
    return {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": f"#{uuid.uuid4()}",
        "type": "Annotation",
        "body": [{
            "type": "TextualBody",
            "value": class_name,
        }],
        "motivation": "classifying",
        "creator": None,
        "created": None,
        "target": {
            "selector": {
                "type": "SvgSelector",
                # https://www.w3.org/TR/annotation-model/#svg-selector
                "value": f"<svg>{svg_path}</svg>",
            }
        }
    }


@app.server.route('/slide/overview/<string:image_id>/annotations.json')
def serve_w3c_annotations(image_id):
    ds = get_dataset()
    image_id = ImageId.from_str(unquote(image_id))
    try:
        annotations: List[Annotation] = ds.annotations[image_id]['annotations']
    except KeyError:
        return abort(404, f"No annotations found for {image_id!r}")

    w3c_annotations = [
        w3c_like_annotation(a.class_name, a.roi)
        for a in annotations
    ]

    return jsonify(w3c_annotations)
