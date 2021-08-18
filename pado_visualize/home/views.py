import json
import sys

from flask import Blueprint
from flask import current_app
from flask import make_response
from flask import render_template

from pado_visualize.data import DatasetState
from pado_visualize.data import dataset
from pado_visualize.extensions import celery
from pado_visualize.oauth import login_required
from pado_visualize.home.tasks import ping_worker_task

# view blueprint for home endpoints
blueprint = Blueprint('home', __name__)


@blueprint.route("/")
@blueprint.route("/index.htm")
@blueprint.route("/index.html")
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

    return render_template("home/index.html", info=info, page_title="Home")


@blueprint.route("/health")
def health():
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route("/ping_worker")
def ping_worker():
    print("...", file=sys.stderr)
    print(celery.conf)
    ping_worker_task.delay()
    print("???", file=sys.stderr)
    return make_response(200, "all good")
