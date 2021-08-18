"""flask app instance submodule"""
from __future__ import annotations

import logging
import sys
from logging.config import dictConfig
from typing import Optional

from flask import Flask

from pado_visualize.data import initialize_dataset
from pado_visualize.extensions import register_extensions

__all__ = ["create_app"]


def create_app(*, configured_app: Optional[Flask] = None, is_worker: bool = False) -> Flask:
    """create a Flask app instance

    Parameters
    ----------
    configured_app:
        provide a preconfigured app in case you want to influence the dynaconf
        based config loading. This is mostly for commandline overwriting.
    is_worker:
        allows to skip blueprint definitions

    """
    configure_logging()

    # allow two step initialization (for cli interface)
    if configured_app is None:
        from pado_visualize.config import initialize_config
        app = Flask("pado_visualize")
        _ = initialize_config(app)
    else:
        app = configured_app

    initialize_dataset(app)

    register_extensions(app, is_worker=is_worker)
    register_blueprints(app, is_worker=is_worker)

    return app


def configure_logging() -> None:
    """configure as early as possible in case we want customization"""
    dictConfig({
        'version': 1,
        'root': {
            'level': 'INFO',
        },
    })
    for logger_name in [
        'pado_visualize.data.caches',
        'pado_visualize.data.dataset',
    ]:
        logger = logging.getLogger(logger_name)
        backend_handler = logging.StreamHandler(sys.stderr)
        backend_handler.setFormatter(
            logging.Formatter('%(name)s::%(levelname)s: %(message)s')
        )
        logger.addHandler(backend_handler)


def register_blueprints(app: Flask, *, is_worker: bool = True) -> None:
    """register all blueprints on the Flask app"""
    # Note: this pattern prevents circular imports, which often occur in larger Flask apps
    # Note: allows us to provide plugin style addons to pado_visualize in the future...

    if is_worker:
        # register the worker tasks
        import pado_visualize.home.tasks
        import pado_visualize.slides.tasks
        return

    # --- views ---
    from pado_visualize.home.views import blueprint as home_blueprint
    from pado_visualize.slides.views import blueprint as slides_blueprint

    app.register_blueprint(home_blueprint, url_prefix="/")
    app.register_blueprint(slides_blueprint, url_prefix="/slides")

    # --- oauth ---
    from pado_visualize.oauth import make_blueprint
    oauth_blueprint = make_blueprint(app)
    if oauth_blueprint:
        app.register_blueprint(oauth_blueprint, url_prefix="/oauth")

    # --- plugins ---
    ...  # todo...
