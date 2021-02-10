import sys

from pado_visualize.wsgi import init_data, init_app


def main():
    import argparse

    # parse commandline
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="debug mode")
    parser.add_argument("dataset_path", nargs='+', help="path to a pado dataset")
    parser.add_argument("--build-thumbnail-cache", action="store_true")
    parser.add_argument("--build-qpzip-cache", action="store_true")
    parser.add_argument("--rebuild-cache", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-auth", action="store_true", help="disable basic authentication")
    args = parser.parse_args()

    init_data(args.dataset_path, cache_path="./.pado_visualize.cache", rebuild=args.rebuild_cache)
    app = init_app()

    if args.build_thumbnail_cache:
        from pado_visualize.routes.thumbnail import _build_thumbnail_cache
        _build_thumbnail_cache()
        return 0
    if args.build_qpzip_cache:
        from pado_visualize.routes.qpzip import _build_qpzip_cache
        _build_qpzip_cache()
        return 0

    if args.no_auth:
        print("RUNNING THE APP WITHOUT AUTHENTICATION", file=sys.stderr)
    else:
        from dash_auth import BasicAuth
        BasicAuth(app, {"user": "pass"})  # fixme

    # run dev server
    return app.run_server(host="127.0.0.1", port=args.port, debug=args.debug)


if __name__ == "__main__":
    sys.exit(main())
