from __future__ import annotations

from flask import Blueprint
from flask import jsonify
from flask import request 
from werkzeug.exceptions import BadRequest

from pado_visualize.data import dataset
from pado_visualize.api.utils import get_filtered_image_ids
from pado_visualize.api.utils import insert_annotation_prediction
from pado_visualize.api.utils import insert_image_prediction


blueprint = Blueprint('api', __name__)

# ---- prediction endpoints ---------------------------------------------------

# TODO: implement tests for this endpoint
# TODO: add authorisation
# TODO: allow filtering by annotation type in get request
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
            return insert_annotation_prediction(prediction_record, image_id)
        else:
            return insert_image_prediction()
    
    elif request.method == 'GET':
        """return all predictions for an image
        
        Note: currently only annotation style predictions have been implemented.
        Once image style predictions are supported this endpoint should be able
        to return a collection of one/both prediction types.
        """

        annotations_df = dataset.annotations[image_id].df
        mask = annotations_df['annotator'].apply(lambda x: x.get('type') == 'model')
        predictions_df = annotations_df[mask]

        return jsonify(predictions_df.to_dict(orient='records')), 200


# ---- filter dataset endpoints -----------------------------------------------
@blueprint.route("/image_ids", methods=['GET'])
def filter_by():
    """return image_ids which match some filter
    
    The filter object must be passed as a json object in the request body.
    Currently, the following key value pairs are supported:
    - "filename": str,
    - "metadata_key": str,
    - "metadata_values": List[str]
    """

    filter = request.get_json()

    try:
        image_ids = get_filtered_image_ids(filter)
    except Exception as e:
        raise BadRequest(f'{e}')

    return jsonify([image_id.to_url_id() for image_id in image_ids]), 200




