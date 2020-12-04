from flask import jsonify

from pado_visualize.app import app
from pado_visualize.data.dataset import get_image_map
from pado_visualize.wsickr.types import Photo
from pado_visualize.wsickr.types import Photos
from pado_visualize.wsickr.types import ResponseGetList
from pado_visualize.wsickr.types import ResponseGetSizes


@app.server.route("/wsickr/get_list.json")
def fake_flickr_photos_get_list():
    num_images = 16
    photos = []
    # for idx, (image_id, pth) in enumerate(get_image_map().items()):
    #     if pth is None or not pth.is_file():
    #        continue

    for image_id, pth in get_image_map().items():
        if pth is None or not pth.is_file():
            continue
        break
    else:
        raise LookupError("nothing there")

    for _ in range(num_images):
        p = Photo(
            id=image_id,
            ownername="SomeOwner",
            tags=" ".join(["tag0", "tag1", "tag2"]),
            title="Organ Slice",
        )
        photos.append(p)
    #    if len(photos) >= num_images:
    #        break
    minimal = ResponseGetList(photos=Photos(photo=photos))

    return jsonify(minimal)
