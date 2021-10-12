from flask import request, Blueprint
from itsdangerous import base64_decode

from pado.images import ImageId

from pado_visualize.data import dataset


blueprint = Blueprint('api', __name__)


@blueprint.route("/<var>/sanity_check")
def sanity_check(var):
    return f'you are sane: {var}', 200

@blueprint.route("/<image_id:image_id>/predictions", methods=['GET', 'POST'])
def manage_predictions(image_id):

    if request.method == 'POST':
        """inserts an annotation into a dataset"""
        prediction_types = ('annotation', 'image')
        payload = request.get_json()
        try:
            prediction_type = payload['prediction_type']
            assert prediction_type in prediction_types, 'Invalid prediction type.'
            prediction_record = payload['prediction']
        except KeyError as e:
            return f'{e}', 400
        except AssertionError as e:
            return f'{e}', 400

        return f'', 200
    
    elif request.method == 'GET':
        """return all predictions for an image"""

        print(dataset.annotations[image_id])

        return '', 200
