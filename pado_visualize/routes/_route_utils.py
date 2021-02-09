from flask import abort
from werkzeug.exceptions import HTTPException

from pado_visualize.data.dataset import get_image_map
from pado.images import ImageId

def _image_path_from_image_id(image_id, abort_if_none=True):
    # convert image_id to path; raise error if the path doesn't resolve
    try:
        im = get_image_map(abort_if_none=True)

        p = None
        try:
            p = im[image_id]
        except KeyError as kerr:
            pass

        try:
            p = im[ImageId.from_str(image_id)]
        except (ValueError, KeyError, TypeError):
            pass

        try:
            p = im[ImageId(image_id)]
        except (ValueError, KeyError):
            pass

        try:
            p = im[ImageId(*image_id.split("__"))]
        except (ValueError, KeyError, AttributeError):
            pass

        if p is None:
            return abort(404, f"image_id {image_id!r} is not in dataset")
        if not p.is_file():
            return abort(404, "image_id resource is not available to server")
        return p
    except HTTPException:
        if abort_if_none:
            raise
        else:
            return None
