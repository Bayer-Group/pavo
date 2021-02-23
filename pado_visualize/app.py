"""flask app instance submodule"""
from __future__ import annotations

import logging
import sys
from importlib import import_module
from logging.config import dictConfig
from pathlib import Path
from typing import Optional

from flask import Flask

# flask app instance
_server: Optional[Flask] = None


def create_plain_server() -> Flask:
    """create a plain Flask app instance

    NOTE: you probably want to call `create_server`
    """
    global _server
    if _server is None:
        _server = Flask(__name__, static_folder='static', static_url_path='/static')
    return _server


def configure_logging(server: Optional[Flask] = None):
    """configure this as early as possible"""

    dictConfig({
        'version': 1,
        'root': {
            'level': 'INFO',
        },
    })
    for logger_name in ['pado_visualize.data.dataset']:
        logger = logging.getLogger(logger_name)
        backend_handler = logging.StreamHandler(sys.stderr)
        backend_handler.setFormatter(
            logging.Formatter('%(name)s::%(levelname)s: %(message)s')
        )
        logger.addHandler(backend_handler)

    if server is not None:
        pass  # TODO: check if we can do late init of logging


def register_extensions(server: Flask) -> None:
    """register all extensions on the Flask app"""
    from pado_visualize.extensions import ImageIdConverter
    # register the image id converter
    server.url_map.converters['image_id'] = ImageIdConverter


def register_blueprints(server: Flask) -> None:
    """register all blueprints on the Flask app"""
    submodule_import_order = [
        'home'
    ]

    # from pado_visualize.routes import init_routes
    # register all routes
    # init_routes()

    for submodule_name in submodule_import_order:
        mod = import_module(f"pado_visualize.{submodule_name}.views")
        # noinspection PyUnresolvedReferences
        server.register_blueprint(mod.blueprint)


def initialize_data(server: Flask) -> None:
    """initialize the dataset"""
    from pado_visualize.data.dataset import (
        init_dataset,
        get_dataset,
        get_metadata,
        get_image_map,
        get_annotation_map,
    )

    # dataset
    init_dataset(
        dataset_paths=list(map(Path, server.config.DATASET_PATHS)),
        persist=True,
        cache_file=server.config.CACHE_PATH,
        ignore_cache=server.config.CACHE_FORCE_REBUILD,
        predictions_csv_file_path=server.config.PREDICTIONS_CSV_FILE,
        predictions_xai_base_path=server.config.PREDICTIONS_XAI_PATH,
    )

    # w = Path(args.wds_path)
    # from pado_visualize.data.webdataset import init_wds
    # init_webdataset(w, persist=True, cache_file=_cache)

    # warm caches
    server.logger.info("warming caches...")
    get_dataset()
    get_image_map()
    get_metadata(filter_dict={})
    get_annotation_map()
    server.logger.info("cashes are lukewarm.")


def create_server(configured_server: Optional[Flask] = None) -> Flask:
    """create a Flask app instance"""

    configure_logging()

    # allow two step initialization (for cli interface)
    if configured_server is None:
        from pado_visualize.config import initialize_config
        server = create_plain_server()
        _ = initialize_config(server)
    else:
        server = configured_server

    initialize_data(server)

    register_extensions(server)
    register_blueprints(server)

    return server


# alias for comfort
create_app = create_server



# def init_app(app: Dash) -> None:
#
#     # configure basic authentication
#     if app.server.config.REQUIRE_AUTH:
#         from dash_auth import BasicAuth
#         BasicAuth(app, app.server.config.USER_PASSWORD_MAP)
#     else:
#         app.server.logger.warning("RUNNING THE APP WITHOUT AUTHENTICATION")


# def init_server() -> Flask:
#   """run everything to return a fully configured flask app"""
#   # NOTE: this will be used by the production server, which should be
#   #   configured by files only.
#   from pado_visualize.app import app, server

#   # NOTE: after this point we access global config settings
#   #   through app.server.config.SETTING, which is why we pass
#   #   the app or app.server instance around.
#   init_config(server)

#   # initialize data
#   init_data(server)

#   # finish initializing the app
#   init_app(app)

#   return app.server

# === instantiate application instance ================================

# app = dash.Dash(
#    __name__,
#    external_stylesheets=[dbc.themes.SANDSTONE],
#    suppress_callback_exceptions=True,
# )
