"""celery tasks for home"""
from celery import Task
from pado_visualize.extensions import celery


@celery.task(bind=True)
def ping_worker_task(self: Task):
    r = self.request
    return {
        "id": r.id,
        "group": r.group,
        "eta": r.eta,
        "retries": r.retries,
    }
