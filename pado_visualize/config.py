from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dynaconf import FlaskDynaconf
from dynaconf import Validator
from flask import Flask

_module_root = Path(__file__).parent


# module layout related settings
class StaticConfig:
    MODULE_ROOT = os.fspath(_module_root)
    TEMPLATE_FOLDER = os.fspath(_module_root / "templates")
    STATIC_FOLDER = os.fspath(_module_root / "static")


def initialize_config(
    app: Flask,
    *,
    override_config: Optional[dict] = None,
    force_env: Optional[str] = None,
) -> FlaskDynaconf:
    """apply configuration to the flask server"""
    dynaconf_config = dict(
        envvar_prefix="PADOVIS",
        settings_file=[".pado_visualize.toml", ".pado_visualize.secrets.toml"],
        core_loaders=['TOML'],
        preload=[],
        validators=[
            Validator("dataset_paths", is_type_of=(list, tuple, str)),
        ],
        default_settings_paths=[],
    )
    if force_env:
        dynaconf_config['env'] = force_env

    flask_config = FlaskDynaconf(app=None, **dynaconf_config)
    flask_config.kwargs["ENV_SWITCHER"] = "PADOVIS_ENV"
    flask_config.kwargs["ENVIRONMENTS"] = True
    flask_config.kwargs["load_dotenv"] = True

    flask_config.init_app(app)

    if override_config is not None:
        for key, value in override_config.items():
            app.config[key] = value

    app.config.from_object(StaticConfig)

    return flask_config
