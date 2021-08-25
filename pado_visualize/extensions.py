"""flask extensions custom to pado_visualize"""
from celery import Celery
from flask_caching import Cache
from flask import Flask

__all__ = [
    "cache",
    "celery",
    "register_extensions",
    "TaskState",
]

# --- proxies ---

celery = Celery()
cache = Cache()


# --- registration ---

def register_extensions(app: Flask, *, is_worker: bool = False) -> None:
    """register all extensions on the Flask app"""

    celery.config_from_object(app.config)
    cache.init_app(app)

    if not is_worker:
        # register the image id converter
        from pado_visualize.utils import ImageIdConverter
        app.url_map.converters['image_id'] = ImageIdConverter

        # register jinja2 globals
        from pado_visualize.utils import url_for_versioned
        app.jinja_env.globals['url_for_versioned'] = url_for_versioned


# --- constants ---

class TaskState:
    SUCCESS = states.SUCCESS
    FAILURE = states.FAILURE
    PROGRESS = "PROGRESS"
    REVOKED = states.REVOKED
    STARTED = states.STARTED
    RECEIVED = states.RECEIVED
    REJECTED = states.REJECTED
    RETRY = states.RETRY
    PENDING = states.PENDING

    @classmethod
    def is_unready(cls, state):
        return state in states.UNREADY_STATES

    @classmethod
    def is_ready(cls, state):
        return state in states.READY_STATES

    @classmethod
    def is_exception(cls, state):
        return state in states.EXCEPTION_STATES

    @classmethod
    def is_propagated(cls, state):
        return state in states.PROPAGATE_STATES
