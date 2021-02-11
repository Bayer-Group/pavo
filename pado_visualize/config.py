import os
from pathlib import Path
from typing import Optional

from dynaconf import FlaskDynaconf, Validator
from flask import Flask


# module layout related settings
class StaticConfig:
    MODULE_ROOT = Path(__file__).parent
    TEMPLATE_FOLDER = MODULE_ROOT / "templates"
    STATIC_FOLDER = MODULE_ROOT / "static"


def initialize_config(
        server: Flask,
        *,
        override_config: Optional[dict] = None,
        force_env: Optional[str] = None
) -> FlaskDynaconf:
    """apply configuration to the flask server"""
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

    server.config.from_object(StaticConfig)

    return flask_config
