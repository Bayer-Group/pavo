"""celery tasks for slides"""
from __future__ import annotations

from celery import group

from pado.images import ImageId
from pado.images.ids import ensure_image_id
from pado_visualize.data import dataset
from pado_visualize.extensions import celery
from pado_visualize.slides.utils import THUMBNAIL_SIZES
from pado_visualize.slides.utils import thumbnail_fs_and_path
from pado_visualize.slides.utils import thumbnail_image


@celery.task
def slide_build_thumbnail_index_task(size: int = 100):
    """build and store an index to the thumbnails"""
    index = dataset.index[:2]

    result = group(
        slide_make_thumbnail_task.signature(image_id, size)
        for image_id in index
    )()
    result.save()
    return {
        'status': 'dispatched',
        'id': result.id,
    }


@celery.task
def slide_make_thumbnail_task(image_id: ImageId, size: int):
    """create a thumnbail and store it"""
    assert size in THUMBNAIL_SIZES
    image_id = ensure_image_id(image_id)
    fs, path = thumbnail_fs_and_path(image_id, size=size, fmt='png')
    if not fs.isfile(path):
        thumbnail_image(
            image_id=image_id,
            image=dataset.images[image_id],
        )
    return {
        'status': 'done',
        'path': path,
    }
