
from flask import Blueprint
from flask import current_app
from flask import render_template
from flask import jsonify

from pado_visualize.data import DatasetState
from pado_visualize.data import dataset
from pado_visualize.oauth import login_required
from pado_visualize.metadata.utils import get_valid_metadata_attribute_options
from pado_visualize.metadata.utils import get_valid_metadata_attributes


# view blueprint for metadata endpoints
blueprint = Blueprint('metadata', __name__)


@blueprint.route("/metadata")
@login_required
def index():
    info = {
        "dataset_paths": current_app.config["DATASET_PATHS"],
        "images": 0,
        "annotations": 0,
        "metadata": 0,
    }
    if dataset.state == DatasetState.READY:
        info["images"] = len(dataset.images)
        info["annotations"] = len(dataset.annotations.df)
        info["metadata"] = len(dataset.metadata.df)
    return render_template("metadata/index.html", info=info, page_title="Metadata")


# ---- metadata endpoints -----------------------------------------------------

@blueprint.route("/metadata/attributes", methods=['GET'])
def metadata_attributes():
    """returns columns of the metadata dataframe"""
    return jsonify(get_valid_metadata_attributes()), 200

@blueprint.route("/metadata/<attribute>/valid_attributes", methods=['GET'])
def valid_metadata_options(attribute):
    """returns a set of unique options for a single metadata attribute in the dataframe"""
    try:
        return jsonify(get_valid_metadata_attribute_options(attribute)), 200
    except Exception as e:
        print(e)
        return f'Error: {e}', 400