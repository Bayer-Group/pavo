from flask import abort

from pado_visualize.data.dataset import get_image_map


def _image_path_from_image_id(image_id):
    # convert image_id to path; raise error if the path doesn't resolve
    im = get_image_map(abort_if_none=True)
    try:
        p = im[image_id]
    except KeyError:
        return abort(404, "image_id is not in dataset")
    if p is None:
        return abort(404, "image_id references a remote image")
    if not p.is_file():
        return abort(404, "image_id resource is not available to server")
    return p
