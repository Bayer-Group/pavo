"""celery tasks for slides"""
from __future__ import annotations

import io

from celery import Task

from pado.images import ImageId
from pado.images.ids import ensure_image_id
from pado.images.utils import IntSize
from pado_visualize.data import DatasetProxy
from pado_visualize.extensions import celery
from pado_visualize.slides.utils import thumbnail_path


@celery.task(bind=True)
def slide_build_thumbnail_index_task(self: Task, size: int = 100):
    """build and store an index to the thumbnails"""
    dataset = DatasetProxy.new_for_worker_access()
    for image_id in dataset.index:
        of = thumbnail_path(image_id, size=size)
        if not of.fs.isfile(of.path):
            slide_make_thumbnail_task.delay(image_id, size)


@celery.task
def slide_make_thumbnail_task(image_id: ImageId, size: int):
    """create a thumnbail and store it"""
    image_id = ensure_image_id(image_id)
    dataset = DatasetProxy.new_for_worker_access()
    of = thumbnail_path(image_id, size=size)
    if of.fs.isfile(of.path):
        return

    img = dataset.images[image_id]
    with img:
        thumb = img.get_thumbnail(IntSize(size, size))
    with io.BytesIO() as f:
        thumb.save(f, format="jpg")
        data = f.getvalue()

    with of.fs.open(of.path, mode="x") as f:
        f.write(data)
    return {
        'status': 'done',
        'path': of.path,
    }
