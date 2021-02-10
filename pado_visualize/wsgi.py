from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from dynaconf import FlaskDynaconf, Validator

if TYPE_CHECKING:
    from flask import Flask


def init_config(server: Flask, *, override_config: Optional[dict] = None):
    """apply configuration to the flask server"""
    dynaconf_config = dict(
        envvar_prefix="PADOVIS",
        settings_file=[".pado_visualize.toml"],
        core_loaders=['TOML'],
        preload=[],
        validators=[
            Validator("annotation_search_dirs", is_type_of=(list, tuple, str)),
        ]
    )

    if override_config is not None:
        dynaconf_config.update(override_config)

    config = FlaskDynaconf(server, **dynaconf_config)
    import sys
    print(config.settings.to_dict(), file=sys.stderr)


def init_data(server: Flask):
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


def init_dash_app(*, override_config: Optional[dict] = None):
    """run everything to return a fully configured plotly dash app

    Parameters
    ----------
    override_config:
        provide a mapping with settings to override. This is
        currently only used to provide a commandline interface
        that allows to easily override defaults

    """
    from pado_visualize.routes import init_routes
    from pado_visualize.app import app, server

    # NOTE: after this point we access global config settings
    #   through app.server.config.SETTING, which is why we pass
    #   the app or app.server instance around.
    init_config(server, override_config=override_config)

    # load the dataset
    init_data(server)

    # register all routes
    init_routes()

    # spawn app
    return app


def init_server():
    """run everything to return a fully configured flask app"""
    # NOTE: this will be used by the production server, which should be
    #   configured by files only.
    server = init_dash_app().server
    return server
