from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from dynaconf import FlaskDynaconf, Validator

if TYPE_CHECKING:
    from dash import Dash
    from flask import Flask


def init_config(
        server: Optional[Flask] = None,
        *,
        override_config: Optional[dict] = None,
        force_env: Optional[str] = None
) -> FlaskDynaconf:
    """apply configuration to the flask server"""

    if server is None:
        from pado_visualize.app import server as _server
        server = _server
        return init_config(server, override_config=override_config, force_env=force_env)

    dynaconf_config = dict(
        envvar_prefix="PADOVIS",
        settings_file=[".pado_visualize.toml", ".pado_visualize.secrets.toml"],
        core_loaders=['TOML'],
        preload=[],
        validators=[
            Validator("annotation_search_dirs", is_type_of=(list, tuple, str)),
        ],
        default_settings_paths=[],
    )
    if force_env:
        dynaconf_config['env'] = force_env

    flask_config = FlaskDynaconf(app=None, **dynaconf_config)
    flask_config.kwargs["ENV_SWITCHER"] = "PADOVIS_ENV"
    flask_config.kwargs["ENVIRONMENTS"] = True
    flask_config.kwargs["load_dotenv"] = True

    flask_config.init_app(server)

    if override_config is not None:
        for key, value in override_config.items():
            server.config[key] = value

    return flask_config


def init_data(server: Flask) -> None:
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
        ignore_cache=server.config.CACHE_FORCE_REBUILD
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


def init_app(app: Dash) -> None:
    from pado_visualize.routes import init_routes

    # register all routes
    init_routes()

    # configure basic authentication
    if app.server.config.REQUIRE_AUTH:
        from dash_auth import BasicAuth
        BasicAuth(app, app.server.config.USER_PASSWORD_MAP)
    else:
        app.server.logger.warning("RUNNING THE APP WITHOUT AUTHENTICATION")


def init_server() -> Flask:
    """run everything to return a fully configured flask app"""
    # NOTE: this will be used by the production server, which should be
    #   configured by files only.
    from pado_visualize.app import app, server

    # NOTE: after this point we access global config settings
    #   through app.server.config.SETTING, which is why we pass
    #   the app or app.server instance around.
    init_config(server)

    # initialize data
    init_data(server)

    # finish initializing the app
    init_app(app)

    return app.server
