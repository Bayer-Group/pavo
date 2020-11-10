import shutil
from pathlib import Path
import tempfile
from typing import Optional

from flask import send_file, abort

# noinspection PyProtectedMember
from tqdm import tqdm

from pado_visualize.data.dataset import get_dataset, get_image_map, get_prediction_map
from palo._scratch.prediction_conversion import (
    xai_inference_pickle_conversion,
    vk_inference_pickle_conversion_from_mb,
)
from paquo.images import QuPathImageType
from paquo.projects import QuPathProject
# noinspection PyUnresolvedReferences
from paquo._cli import qpzip_project

from pado_visualize.app import app


def _build_qpzip_cache():
    pm = get_prediction_map()
    image_ids_with_predictions = [k for k, v in pm.items() if v]
    for image_id in tqdm(image_ids_with_predictions):
        _get_project_qpzip(image_id)


def _get_project_qpzip(image_id) -> Optional[Path]:
    ds = get_dataset()
    qpzip_dir = ds.path / "qpzip"
    qpzip_dir.mkdir(exist_ok=True)

    qpzip_path = qpzip_dir / f"{image_id}.qpzip"
    if qpzip_path.is_file():
        return qpzip_path

    im = get_image_map()
    image = im[image_id]

    predictions_dir = ds.path / "predictions" / image_id
    if not predictions_dir.is_dir():
        return None

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_path = Path(tmp_dir) / "pado_project"

        with QuPathProject(project_path, mode='x') as qp:
            # add an image
            entry = qp.add_image(
                image,
                image_type=QuPathImageType.BRIGHTFIELD_H_E
            )

            for mb_prediction in sorted(predictions_dir.glob("heat_map_*.pckl")):
                name = mb_prediction.stem[len("heat_map_"):]
                # iterate over the image in a grid pattern
                for tile_obj_kwargs in xai_inference_pickle_conversion(
                    mb_prediction,
                    vres=16,
                    map_name=name
                ):
                    _ = entry.hierarchy.add_tile(**tile_obj_kwargs)

            for vk_prediction in sorted(predictions_dir.glob("VK_model_pred.pckl")):
                for tile_obj_kwargs in vk_inference_pickle_conversion_from_mb(vk_prediction):
                    _ = entry.hierarchy.add_tile(**tile_obj_kwargs)

            print("added", len(entry.hierarchy.detections), "tiles")

        qpzip_project(project_path)
        shutil.move(project_path.with_suffix(".qpzip"), qpzip_path)

    return qpzip_path


@app.server.route("/qpzip/<image_id>.qpzip")
def serve_qpzip(image_id):
    # FIXME: this must be done by a worker process and not in this endpoint
    #   - simple to do as soon as higher priority todos are completed

    qpzip = _get_project_qpzip(image_id)
    if qpzip is None:
        return abort(404, "no predictions available")

    return send_file(
        qpzip.open("rb"),
        mimetype="application/x-pado-qpzip",
        as_attachment=True,
        attachment_filename=qpzip.name,
    )
