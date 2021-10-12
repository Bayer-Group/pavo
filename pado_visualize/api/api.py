from flask import request, Blueprint

from pado.annotations import Annotation

from pado_visualize.data import dataset


blueprint = Blueprint('api', __name__)


@blueprint.route("/<var>/sanity_check")
def sanity_check(var):
    return f'you are sane: {var}', 200

@blueprint.route("/<image_id:image_id>/predictions", methods=['GET', 'POST'])
def manage_predictions(image_id):
    """endpoint to manipulate image predictions"""

    if request.method == 'POST':
        """inserts an annotation into a dataset"""
        prediction_types = ('annotation', 'image')
        payload = request.get_json()
        try:
            prediction_type = payload['prediction_type']
            assert prediction_type in prediction_types, 'Invalid prediction type.'

            prediction_record = payload['prediction']

        except KeyError as e:
            return f'KeyError on {e}', 400
        except AssertionError as e:
            return f'{e}', 400

        a = Annotation.from_obj(prediction_record)

        print(len(dataset.annotations[image_id].df))
        dataset.annotations[image_id].insert(index=0, value=a)
        print(len(dataset.annotations[image_id].df))

        return f'', 200
    
    elif request.method == 'GET':
        """return all predictions for an image"""

        # TODO: figure out how to filter annotations by annotator.type=='model'
        # TODO: further filter by predictions by prediction types
        return str(dataset.annotations[image_id]), 200
