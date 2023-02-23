from __future__ import annotations

from flask import Blueprint
from flask import jsonify
from flask import render_template

from pavo.data import dataset
from pavo.metadata.utils import get_valid_metadata_attribute_options
from pavo.metadata.utils import get_valid_metadata_attributes
from pavo.oauth import login_required

# view blueprint for metadata endpoints
blueprint = Blueprint("metadata", __name__)


@blueprint.route("/metadata")
@login_required
def index():
    table = dataset.get_tabular_records()
    return render_template(
        "metadata/index.html",
        page_title="Metadata",
        metadata=table.to_dict("records"),
    )


# ---- metadata endpoints -----------------------------------------------------


@blueprint.route("/metadata/attributes", methods=["GET"])
def metadata_attributes():
    """returns columns of the metadata dataframe"""
    return jsonify(get_valid_metadata_attributes()), 200


@blueprint.route("/metadata/<attribute>/valid_attributes", methods=["GET"])
def valid_metadata_options(attribute):
    """returns a set of unique options for a single metadata attribute in the dataframe"""
    try:
        return jsonify(get_valid_metadata_attribute_options(attribute)), 200
    except Exception as e:
        print(e)
        return f"Error: {e}", 400
