from pado_visualize.app import app
from pado_visualize.dataloader import image_id_to_image_path
from pado_visualize.data.slides import TifffileDeepZoomGenerator


@app.server.before_first_request
def slide_init():
    app.server.slides = {}


def _get_deep_zoom(image_id: str) -> TifffileDeepZoomGenerator:
    try:
        dz = app.server.slides[image_id]
    except KeyError:
        # we should take a lock here... but let's move quick to meet the deadline
        # fixme: not good in multiuser scenario
        try:
            image_path = image_id_to_image_path(image_id)
        except RuntimeError:
            return abort(500, "no data available")
        except FileNotFoundError:
            return abort(404, "image_id doesn't match local file")
        else:
            dz = app.server.slides[image_id] = TifffileDeepZoomGenerator(image_path)
    return dz


@app.server.route('/slide/<str:image_id>/image.dzi')
def slide_dzi(image_id):
    dz = _get_deep_zoom(image_id)

    resp = make_response(dz.get_dzi())
    resp.mimetype = 'application/xml'
    return resp


@app.server.route('/slide/<str:image_id>_files/<int:level>/<int:col>_<int:row>.jpeg')
def slide_tile(image_id, level, col, row):
    dz = _get_deep_zoom(image_id)
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
        return abort(500, "not implemented tile request")

    resp = make_response(tile)
    resp.mimetype = 'image/%s' % format
    return resp
