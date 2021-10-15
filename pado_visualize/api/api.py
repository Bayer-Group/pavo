import pandas as pd

from flask import request, Blueprint, jsonify

from pado.images import ImageId, image
from pado.annotations import Annotation

from pado_visualize.data import dataset


blueprint = Blueprint('api', __name__)


# ---- prediction api ----------------------------------------------------------

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

# ---- prediction api helper functions -----------------------------------------
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


# ---- general api queries -----------------------------------------------------
@blueprint.route("/image_ids", methods=['GET'])
def filter_by_image_id():
    """filtering"""

    filename = request.args.get('filename', None)
    metadata_key = request.args.get('metadata_key', None)
    metadata_value = request.args.get('metadata_value', None)

    if request.args == {}:
        image_id_strings = list(dataset.images.df.index)
        image_ids = [ImageId.from_str(id_string) for id_string in image_id_strings]
        return jsonify([image_id.to_url_id() for image_id in image_ids]), 200
    elif filename:
        # TODO: more fuzzy matching (regex maybe)
        image_id_strings = list(dataset.images.df.index)
        image_ids = [ImageId.from_str(id_string) for id_string in image_id_strings]
        matched = [image_id.to_url_id() for image_id in image_ids if image_id.last == filename]
        return jsonify(matched), 200
    elif metadata_key and metadata_value:
        try:
            image_id_strings = (dataset.metadata.df[metadata_key] == metadata_value).index.unique()
        except:
            # TODO make this error better
            return '', 400
        
        image_ids = [ImageId.from_str(id_string) for id_string in image_id_strings]
        matched = [image_id.to_url_id() for image_id in image_ids]
        return jsonify(matched), 200


@blueprint.route("/metadata/finding_types", methods=['GET'])
def request_metadata_finding_types():

    return jsonify(dataset.metadata.df['finding_type'].apply(pd.Series).stack().reset_index(drop=True).unique().tolist()), 200






# @blueprint.route("image_ids/<string:filename>", methods=['GET'])
# def filter_by_filename(filename):
#     """checks if image exists based on filename
    
#     Note: There could be more than one image with a matching filename"""

#     try:
#         site = request.args.get('site')
#     except KeyError as e:
#         return 'Did not provide site', 400
    
#     image_ids = []
#     # TODO: this is terrible but it currently not easy to check ImageId equality
#     for image_id_string in list(dataset.images.df.index):
#         image_id = ImageId.from_str(image_id_string)
#         image_identifier = (image_id.last, image_id.site)
#         if image_identifier == (filename, site):
#             image_ids.append(image_id_string)
    
#     if image_ids:
#         return jsonify(image_ids), 200
#     else:
#         # (filename, site) does not exist
#         return '', 404
