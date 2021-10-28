"""flask extensions custom to pado_visualize"""
import logging

import orjson
from celery import Celery
from celery import states
from flask import Flask
from flask import current_app
from flask import render_template
from flask.json import dumps as flask_json_dumps
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

        # use orjson as our default json encoder
        app.json_encoder = ORJSONEncoder
        app.json_decoder = ORJSONDecoder


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
            "jsglue/js_bridge.js", namespace=type(self).__name__, rules=flask_json_dumps(routes)
        )


class ORJSONEncoder:
    """an orjson based encoder

    References
    ----------
    - https://stackoverflow.com/a/63516680/2564895
    - https://github.com/ijl/orjson/issues/195

    """

    def __init__(
        self,
        *,
        skipkeys=False,
        ensure_ascii=True,
        check_circular=True,
        allow_nan=True,
        indent=None,
        separators=None,
        default=None,
        sort_keys=True,
        **kwargs
    ):
        """setting up the orjson config"""
        # checking unused defaults and extra kwargs
        if skipkeys is not False:
            logging.warning(f"{type(self).__name__} ignores skipkeys={skipkeys!r}")
        if ensure_ascii is not True:
            logging.warning(f"{type(self).__name__} ignores ensure_ascii={ensure_ascii!r}")
        if check_circular is not True:
            logging.warning(f"{type(self).__name__} ignores check_circular={check_circular!r}")
        if allow_nan is not True:
            logging.warning(f"{type(self).__name__} ignores allow_nan={allow_nan!r}")
        if not (separators is None or tuple(separators) == (",", ":")):
            logging.warning(f"{type(self).__name__} ignores separators={separators!r}")
        if kwargs:
            logging.error(f"{type(self).__name__} called with extra kwargs: {kwargs!r}")

        # collecting options
        flags = (
            0
            | orjson.OPT_SERIALIZE_NUMPY
            # | orjson.OPT_SERIALIZE_DATACLASS  # default in v3.x
            # | orjson.OPT_SERIALIZE_UUID  # default in v3.x
        )
        if indent:
            flags |= orjson.OPT_INDENT_2  # just use 2 always
        if sort_keys:
            flags |= orjson.OPT_SORT_KEYS

        self._default = default
        self._flags = flags

    def encode(self, obj):
        """encode using orjson"""
        return orjson.dumps(obj, option=self._flags, default=self._default).decode('utf-8')


class ORJSONDecoder:
    """an orjson based decoder

    Notes
    -----
    The decoder needs to be able to handle object_hook due to the way
    flask.json.tag.TaggedJSONSerializer works:
    https://github.com/pallets/flask/blob/main/src/flask/json/tag.py#L312

    References
    ----------
    - https://stackoverflow.com/a/63516680/2564895
    - https://github.com/ijl/orjson/issues/195

    """

    def __init__(
        self,
        *,
        object_hook=None,
        parse_float=None,
        parse_int=None,
        parse_constant=None,
        strict=True,
        object_pairs_hook=None,
        **kwargs
    ):
        """parse the orjson decoder config"""
        # checking unused defaults and extra kwargs
        if parse_float is not None:
            logging.warning(f"{type(self).__name__} ignores parse_float={parse_float!r}")
        if parse_int is not None:
            logging.warning(f"{type(self).__name__} ignores parse_int={parse_int!r}")
        if parse_constant is not None:
            logging.warning(f"{type(self).__name__} ignores parse_constant={parse_constant!r}")
        if strict is not True:
            logging.warning(f"{type(self).__name__} ignores strict={strict!r}")
        if kwargs:
            logging.error(f"{type(self).__name__} called with extra kwargs: {kwargs!r}")

        if object_pairs_hook is not None:
            # todo: maybe raise here, so we catch it early...
            logging.error(f"{type(self).__name__} called with object_pairs_hook={object_pairs_hook!r}")

        self._object_hook = object_hook

    def decode(self, obj):
        """decode using orjson"""
        data = orjson.loads(obj)
        if self._object_hook:
            return self._object_hook(data)
        else:
            return data
