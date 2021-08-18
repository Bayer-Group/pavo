"""background tasks in pado_visualize

TODO: autolaunch those on cmdline invocation

"""
from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from celery import Celery
from celery import Task

if TYPE_CHECKING:
    from flask import Flask


def initialize_celery(app: Optional[Flask] = None) -> Celery:
    """create the base object for queue based background tasks"""
    if app is None:
        from pado_visualize.app import create_app
        app = create_app(is_worker=True)

    # noinspection PyAbstractClass
    class ContextTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_BACKEND"],
        broker=app.config["CELERY_BROKER_URL"],
        task_cls=ContextTask,
    )
    celery.conf.update(app.config)
    assert not hasattr(app, 'celery')
    app.celery = celery  # set attribute on app instance
    return celery


celery = initialize_celery()


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    pass
