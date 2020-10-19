import json

from celery.result import AsyncResult
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import render_template
from flask import url_for

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
    description = {
        "path": current_app.config["DATASET_PATHS"],
        "num_images": 0,
        "num_annotations": 0,
    }
    if dataset.state == DatasetState.READY:
        description = dataset.describe(output_format='json')

    return render_template("home/index.html", info=description, page_title="Home")


@blueprint.route("/health")
def health():
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@blueprint.route("/worker/ping")
def ping_worker():
    result: AsyncResult = ping_worker_task.apply_async()
    return jsonify({
        'status': 200,
        'id': result.id,
        'link': url_for('home.pong_worker', task_id=result.id)
    })


@blueprint.route("/worker/<string:task_id>/pong")
def pong_worker(task_id):
    result = AsyncResult(task_id, app=celery)
    return jsonify({
        'id': task_id,
        'status': result.state,
        'info': str(result.info),
    })
