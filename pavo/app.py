"""flask app instance submodule"""
from __future__ import annotations

import logging
import sys
import time
from logging.config import dictConfig
from typing import Optional

from flask import Flask
from flask import Response
from flask import g

from pavo.data import initialize_dataset
from pavo.extensions import register_extensions

__all__ = ["create_app"]


def create_app(
    *,
    configured_app: Optional[Flask] = None,
    is_worker: bool = False,
    config_only: bool = False,
) -> Flask:
    """create a Flask app instance

    Parameters
    ----------
    configured_app:
        provide a preconfigured app in case you want to influence the dynaconf
        based config loading. This is mostly for commandline overwriting.
    is_worker:
        allows to skip blueprint definitions
    config_only:
        return the app directly after configuring

    """
    configure_logging()

    # allow two-step initialization (for cli interface)
    if configured_app is None:
        from pavo.config import initialize_config

        app = Flask("pavo")
        _ = initialize_config(app)
    else:
        app = configured_app

    if config_only:
        return app

    initialize_dataset(app)

    register_extensions(app, is_worker=is_worker)
    register_blueprints(app, is_worker=is_worker)
    register_decorators(app, is_worker=is_worker)

    return app


def configure_logging() -> None:
    """configure as early as possible in case we want customization"""
    dictConfig(
        {
            "version": 1,
            "root": {
                "level": "INFO",
            },
        }
    )
    for logger_name in [
        "pavo.data.caches",
        "pavo.data.dataset",
    ]:
        logger = logging.getLogger(logger_name)
        backend_handler = logging.StreamHandler(sys.stderr)
        backend_handler.setFormatter(
            logging.Formatter("%(name)s::%(levelname)s: %(message)s")
        )
        logger.addHandler(backend_handler)


def register_blueprints(app: Flask, *, is_worker: bool = True) -> None:
    """register all blueprints on the Flask app"""
    # Note: this pattern prevents circular imports, which often occur in larger Flask apps
    # Note: allows us to provide plugin style addons to pavo in the future...

    if is_worker:
        # register the worker tasks
        import pavo.home.tasks  # noqa: F401
        import pavo.slides.tasks  # noqa: F401

        return

    # --- views ---
    from pavo.home.views import blueprint as home_blueprint
    from pavo.metadata.views import blueprint as metadata_blueprint
    from pavo.slides.views import blueprint as slides_blueprint

    app.register_blueprint(home_blueprint, url_prefix="/")
    app.register_blueprint(metadata_blueprint, url_prefix="/metadata")
    app.register_blueprint(slides_blueprint, url_prefix="/slides")

    # --- api ---
    from pavo.api.api import blueprint as api_blueprint

    app.register_blueprint(api_blueprint, url_prefix="/api")

    # --- plugins ---
    ...  # todo...


def register_decorators(app: Flask, *, is_worker: bool = True) -> None:
    """register useful decorators"""
    if is_worker:
        return

    @app.before_request
    def calculate_timing() -> None:
        t0 = time.monotonic()
        g.get_request_duration = lambda: time.monotonic() - t0

    @app.after_request
    def set_timing_header(response: Response) -> Response:
        response.headers["x-pado-request-duration"] = g.get_request_duration()
        return response
