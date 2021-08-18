from __future__ import annotations

import argparse
import os
import os.path
import sys
import warnings
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from flask import Flask

from pado_visualize.app import create_app
from pado_visualize.config import initialize_config
from pado_visualize import __version__

if TYPE_CHECKING:
    from dynaconf import LazySettings


def print_config(settings: LazySettings) -> None:
    """print the current app config to console"""
    from dynaconf.utils import files as _files

    # note: SEARCHTREE is updated after configure
    searchtree: List[str] = getattr(_files, 'SEARCHTREE', [])

    settings_files = []
    for location in searchtree:
        files = [
            file
            for file in settings.settings_file
            if os.path.isfile(os.path.join(location, file))
        ]
        settings_files.append((location, files))

    output = [
        "### SEARCHTREE ###",
        "\n".join(f"{'*' if files else ' '} {loc} {','.join(files)}" for loc, files in settings_files),
        "",
        f"### CONFIGURATION using env '{settings.current_env}' ###",
        "\n".join(f"  {k} = {v!r}" for k, v in settings.as_dict().items()),
    ]
    print("\n".join(output))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true", help="run in production")
    parser.add_argument("--show-config", action="store_true", help="print config to console")
    parser.add_argument("--debug", action="store_const", const=True, help="debug mode")
    parser.add_argument("--cache-path", type=str, help="cache path for dataset")
    parser.add_argument("--host", type=str, help="ip or hostname")
    parser.add_argument("--port", type=int, help="override port")
    parser.add_argument("--version", action="store_true", help="print version")
    parser.add_argument("dataset_paths", nargs='*', help="path to a pado dataset")

    if argv is not None:
        argv = argv[1:]  # allow
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    overrides = {
        setting: getattr(args, key)
        for setting, key in {
            ('DEBUG', 'debug'),
            ('CACHE_PATH', 'cache_path'),
            ('SERVER', 'host'),
            ('PORT', 'port'),
            ('DATASET_PATHS', 'dataset_paths'),
        }
        if getattr(args, key)
    }

    # selected env config
    env = 'production' if args.production else None

    # acquire the configuration
    app = Flask("pado_visualize")
    settings = initialize_config(app=app, override_config=overrides, force_env=env).settings

    if args.show_config:
        print_config(settings)
        return 0

    if not settings.DATASET_PATHS:
        warnings.warn("no DATASET_PATHS specified! (set via cmdline in dev or file in prod)")

    if settings.current_env.lower() == "development":
        # run development app
        app = create_app(configured_app=app)
        app.run(
            host=app.config.SERVER,
            port=app.config.PORT,
            debug=app.config.DEBUG
        )
        return 0

    elif settings.current_env.lower() == "production":
        print("dispatching to uwsgi:")
        os.execvp(
            file="uwsgi",
            args=[
                "uwsgi",
                "--http", f"{settings.SERVER}:{settings.PORT}",
                "--env", f"PADOVIS_ENV={settings.current_env}",
                "--manage-script-name",
                "--mount", "/=pado_visualize.app:create_app()",
                "--lazy-apps",  # prevent locks due to too aggressive memory sharing
                "--master",
                "--processes", f"{settings.UWSGI_NUM_PROCESSES}"
            ],
        )

    else:
        print(f"ERROR: unsupported environment '{settings.current_env}'", file=sys.stderr)
        return -1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
