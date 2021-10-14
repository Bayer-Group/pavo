from flask import request, Blueprint, jsonify

from pado.images import ImageId
from pado.annotations import Annotation

from pado_visualize.data import dataset


blueprint = Blueprint('api', __name__)


# TODO: implement tests for this endpoint
# TODO: add authorisation
@blueprint.route("/<image_id:image_id>/predictions", methods=['GET', 'POST'])
def manage_predictions(image_id):
    """endpoint to manipulate image predictions"""

    prediction_types = ('annotation', 'image')

    if request.method == 'POST':
        data = request.get_json()
        try:
            prediction_type = data['prediction_type']
            prediction_record = data['prediction']
        except KeyError as e:
            return f'KeyError: {e} is required.', 400
        
        if prediction_type not in prediction_types:
            return f'Prediction type "{prediction_type}" is invalid.', 400
        
        if prediction_type == "annotation":
            return _insert_annotation_prediction(prediction_record, image_id)
        else:
            return _insert_image_prediction()
    
    elif request.method == 'GET':
        """return all predictions for an image
        
        Note: currently only annotation style predictions have been implemented.
        Once image style predictions are supported this endpoint should be able
        to return a collection of one/both prediction types.
        
        # TODO: allow filtering by annotation type
        """

        annotations_df = dataset.annotations[image_id].df
        mask = annotations_df['annotator'].apply(lambda x: x.get('type') == 'model')
        predictions_df = annotations_df[mask]

        return jsonify(predictions_df.to_dict(orient='records')), 200

# ---- helper functions --------------------------------------------------------
def _insert_annotation_prediction(prediction_record: dict, image_id: ImageId):
    """inserts an annotation style prediction into an image's list of annotations"""

    if prediction_record['annotator']['type'] != 'model':
        return f'Annotator type for predictions must be "model"', 400 

    try:
        dataset.annotations[image_id].insert(
            index=0, 
            value=Annotation.from_obj(prediction_record)
        )
    except Exception as e:
        return f'Could not insert prediction for {image_id} due to {e}', 500

    return '', 200

def _insert_image_prediction():
    # TODO: upload a large image style prediction here
    return 'not implemented', 200
