"""celery tasks for home"""
from pado_visualize.extensions import celery


@celery.task
def ping_worker_task():
    return "hello world!"
