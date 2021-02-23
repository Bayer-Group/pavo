import argparse
import sys
import textwrap
from typing import List, Optional

from pado_visualize.app import app, server
from pado_visualize.wsgi import init_app, init_data, init_config


def _print_config(settings):
    """print the current app config to console"""
    from dynaconf.utils import files as _files

    # note: SEARCHTREE is updated after configure
    searchtree: List[str] = getattr(_files, 'SEARCHTREE', [])
    print("### SEARCHTREE ###")
    for location in searchtree:
        print(f"  {location}")
    print(f"\n### CONFIGURATION using env '{settings.current_env}' ###")
    for key, value in settings.as_dict().items():
        print(f"  {key} = {repr(value)}")


def main(argv: Optional[List[str]] = None) -> int:
    # parse commandline
    # TODO: I need to rework this and make it more intuitive...
    #   right now this is just to enable basic cli override support
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true", help="run in production")
    parser.add_argument("--show-config", action="store_true", help="print config to console")
    # parser.add_argument("--build-thumbnail-cache", action="store_true")
    # parser.add_argument("--build-qpzip-cache", action="store_true")
    parser.add_argument("--debug", action="store_const", const=True, help="debug mode")
    parser.add_argument("--cache-force-rebuild", action="store_const", const=True)
    parser.add_argument("--cache-path", type=str, help="cache path for dataset")
    parser.add_argument("--server", type=str, help="server ip or hostname")
    parser.add_argument("--port", type=int, help="override port")
    parser.add_argument(
        "--no-auth",
        dest="require_auth",
        action="store_const",  # NOTE because dest is inverted, the logic is inverted here
        const=False,
        help="disable basic authentication"
    )
    parser.add_argument("dataset_paths", nargs='*', help="path to a pado dataset")

    if argv is not None:
        argv = argv[1:]

    args = parser.parse_args(argv)

    overrides = {
        key.upper(): getattr(args, key)
        for key in {'debug', 'cache_force_rebuild', 'cache_path', 'server', 'port', 'require_auth', 'dataset_paths'}
        if getattr(args, key)
    }

    env = None  # use config
    if args.production:
        if overrides:
            print("can't specify overrides in production. please set in config file `.pado_visualize.local.toml`")
            return -1
        env = 'production'

    # acquire the configuration
    settings = init_config(server=server, override_config=overrides, force_env=env).settings

    if args.show_config:
        _print_config(settings)
        return 0

    if settings.REQUIRE_AUTH and not settings.USER_PASSWORD_MAP:
        msg = textwrap.dedent("""\
            ERROR: user authentication requested but no USER_PASSWORD_MAP defined!

            Please create a file called `.pado_visualize.secrets.toml`:
            ```
            [default.USER_PASSWORD_MAP]
            someusername = ThEpAsSWord1
            anotherone = 12345supersecret
            ```
        """)
        print(msg)
        return -1

    # if args.build_thumbnail_cache:
    #    from pado_visualize.routes.thumbnail import _build_thumbnail_cache
    #    _build_thumbnail_cache()
    #    return 0
    # if args.build_qpzip_cache:
    #    from pado_visualize.routes.qpzip import _build_qpzip_cache
    #    _build_qpzip_cache()
    #    return 0

    if not settings.DATASET_PATHS:
        print("no DATASET_PATHS specified! (set via cmdline in dev or file in prod)", file=sys.stderr)
        return -1

    if settings.current_env.lower() == "development":
        # run development server
        init_data(server=server)
        init_app(app)
        return app.run_server(
            host=app.server.config.SERVER,
            port=app.server.config.PORT,
            debug=app.server.config.DEBUG
        )

    elif settings.current_env.lower() == "production":
        import os
        os.execvp(
            file="uwsgi",
            args=[
                "uwsgi",
                "--http", f"{settings.SERVER}:{settings.PORT}",
                "--env", f"PADOVIS_ENV={settings.current_env}",
                "--manage-script-name",
                "--mount", "/=pado_visualize.wsgi:init_server()",
                "--lazy-apps",  # prevent looks due to too aggressive memory sharing
                "--master",
                "--processes", f"{settings.UWSGI_NUM_PROCESSES}"
            ],
        )

    else:
        print(f"UNSUPPORTED ENVIRONMENT '{settings.current_env}'")
        return -1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
