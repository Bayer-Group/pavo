
from flask import Blueprint
from flask import current_app
from flask import render_template

from pado_visualize.data import DatasetState
from pado_visualize.data import dataset
from pado_visualize.oauth import login_required

# view blueprint for home endpoints
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
