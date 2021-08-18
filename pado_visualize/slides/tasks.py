"""celery tasks for slides"""
from pado.images import ImageId
from pado.images.utils import IntSize
from pado_visualize.data import dataset
from pado_visualize.extensions import celery
from pado_visualize.slides.utils import thumbnail_path


@celery.task
def slide_build_thumbnail_index_task(size: int = 100):
    """build and store an index to the thumbnails"""
    for image_id in dataset.index:
        of = thumbnail_path(image_id, size=size)
        if not of.fs.isfile(of.path):
            slide_make_thumbnail_task.delay(image_id, size)


@celery.task
def slide_make_thumbnail_task(image_id: ImageId, size: int):
    of = thumbnail_path(image_id, size=size)
    if of.fs.isfile(of.path):
        return

    img = dataset.images[image_id]
    thumb = img.get_thumbnail(IntSize(size, size))
    with of.fs.open(of.path, mode="x") as f:
        thumb.save(f, format="jpg")
