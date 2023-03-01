"""celery tasks for home"""
from __future__ import annotations

from celery import Task

from pavo.extensions import celery


@celery.task(bind=True)
def ping_worker_task(self: Task) -> dict:
    r = self.request
    return {
        "id": r.id,
        "group": r.group,
        "eta": r.eta,
        "retries": r.retries,
    }
