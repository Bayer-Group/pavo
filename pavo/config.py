from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import ContextManager
from typing import Optional

if sys.version_info >= (3, 9):
    from importlib.resources import as_file
    from importlib.resources import files
else:
    from importlib_resources import as_file
    from importlib_resources import files

from dynaconf import FlaskDynaconf
from dynaconf import Validator

if TYPE_CHECKING:
    from flask import Flask

__all__ = [
    "default_config_as_file",
    "initialize_config",
]


_module_root = Path(__file__).parent


# module layout related settings
class StaticConfig:
    MODULE_ROOT = os.fspath(_module_root)
    TEMPLATE_FOLDER = os.fspath(_module_root / "templates")
    STATIC_FOLDER = os.fspath(_module_root / "static")


def default_config_as_file() -> ContextManager[Path]:
    """acquire default config as file"""
    return as_file(files("pavo").joinpath(".pavo.default.toml"))


def initialize_config(
    app: Flask,
    *,
    override_config: Optional[dict] = None,
    force_env: Optional[str] = None,
) -> FlaskDynaconf:
    """apply configuration to the flask server"""
    dynaconf_config: dict[str, Any] = dict(
        ENVVAR_PREFIX="PAVO",
        settings_file=[".pavo.toml", ".pavo.secrets.toml"],
        core_loaders=["TOML"],
        validators=[
            Validator("dataset_paths", is_type_of=(list, tuple, str)),
        ],
        default_settings_paths=[],
    )

    dynaconf_config["ENV_SWITCHER"] = "PAVO_ENV"
    dynaconf_config["ENVIRONMENTS"] = True
    dynaconf_config["load_dotenv"] = True

    if force_env:
        # fixme: dynaconf_config['env'] = force_env
        os.environ["PAVO_ENV"] = force_env

    with default_config_as_file() as default:
        flask_config = FlaskDynaconf(
            app=None,
            preload=[os.fspath(default.absolute())],
            **dynaconf_config,
        )
        flask_config.init_app(app)

    if override_config is not None:
        for key, value in override_config.items():
            app.config[key] = value

    app.config.from_object(StaticConfig)

    return flask_config
