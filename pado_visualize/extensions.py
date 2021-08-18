"""flask extensions custom to pado_visualize"""
from celery import Celery
from flask_caching import Cache
from flask import Flask

__all__ = [
    "cache",
    "celery",
    "register_extensions",
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
