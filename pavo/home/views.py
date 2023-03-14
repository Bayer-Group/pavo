from __future__ import annotations

import json

from celery.result import AsyncResult
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import render_template
from flask import url_for

from pavo._types import EndpointResponse
from pavo.data import DatasetState
from pavo.data import dataset
from pavo.extensions import celery
from pavo.home.tasks import ping_worker_task

# view blueprint for home endpoints
blueprint = Blueprint("home", __name__)


@blueprint.route("/")
@blueprint.route("/index.htm")
@blueprint.route("/index.html")
def index() -> EndpointResponse:
    description = {
        "path": current_app.config["DATASET_PATHS"],
        "num_images": 0,
        "num_annotations": 0,
    }
    if dataset.state == DatasetState.READY:
        description = dataset.describe()

    return render_template("home/index.html", info=description, page_title="Home")


@blueprint.route("/health")
def health() -> EndpointResponse:
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@blueprint.route("/worker/ping")
def ping_worker() -> EndpointResponse:
    result: AsyncResult = ping_worker_task.apply_async()
    return jsonify(
        {
            "status": 200,
            "id": result.id,
            "link": url_for("home.pong_worker", task_id=result.id),
        }
    )


@blueprint.route("/worker/<string:task_id>/pong")
def pong_worker(task_id: str) -> EndpointResponse:
    result = AsyncResult(task_id, app=celery)
    return jsonify(
        {
            "id": task_id,
            "status": result.state,
            "info": str(result.info),
        }
    )
