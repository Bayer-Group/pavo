import uuid
from typing import List
from urllib.parse import unquote

from flask import jsonify, abort

from pado.annotations import Annotation
from pado.images import ImageId
from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset


def w3c_like_annotation(class_name, region, r_g_b=None):
    """make a w3c annotation like annotation"""
    return {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": f"#{uuid.uuid4()}",
        "type": "Annotation",
        "body": [{
            "type": "TextualBody",
            "value": class_name,
        }],
        "target": {
            "selector": {
                "type": "SvgSelector",
                "value": f"<svg>{region.svg()}</svg>",
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
