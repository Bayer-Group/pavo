"""flask extensions custom to pado_visualize"""
import json

from celery import Celery
from celery import states
from flask import Flask
from flask import current_app
from flask import render_template
from flask_caching import Cache
from flask_jsglue import JSGlue
from flask_jsglue import get_routes

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

        # register custom JSGlue
        ServerRoutesJS().init_app(app)


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


# --- extras ---

class ServerRoutesJS(JSGlue):

    def init_app(self, app):

        @app.route("/server_routes.js")
        def serve_js():
            return self.generate_js(), 200, {'Content-Type': 'text/javascript'}

        @app.context_processor
        def context_processor():
            return {type(self).__name__: type(self)}

    def generate_js(self):
        routes = get_routes(current_app or self.app)
        # noinspection PyUnresolvedReferences
        return render_template(
            "jsglue/js_bridge.js", namespace=type(self).__name__, rules=json.dumps(routes)
        )
