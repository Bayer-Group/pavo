"""background tasks in pado_visualize

TODO: autolaunch those on cmdline invocation

"""
from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from celery import Celery
from celery import Task
from celery.signals import celeryd_init

if TYPE_CHECKING:
    from flask import Flask


def initialize_celery(app: Optional[Flask] = None) -> Celery:
    """create the base object for queue based background tasks"""
    if app is None:
        from pado_visualize.app import create_app
        app = create_app(is_worker=True)

    class ContextTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    c = Celery(
        app.import_name,
        backend=app.config["result_backend"],
        broker=app.config["broker_url"],
        task_cls=ContextTask,
    )
    c.conf.update(app.config)
    assert not hasattr(app, 'celery')
    app.celery = c  # set attribute on app instance
    return c


celery = initialize_celery()


# --- signals and events ---

@celeryd_init.connect
def configure_workers(sender=None, conf=None, **kwargs):
    pass


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    pass


@celery.on_after_finalize.connect
def setup_one_off_tasks(sender, **kwargs):
    from pado_visualize.slides.tasks import slide_build_thumbnail_index_task
    slide_build_thumbnail_index_task.apply_async()
