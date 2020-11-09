from pathlib import Path


def init_data(dataset_path: str, cache_path: str):
    from pado_visualize.data.dataset import init_dataset

    # dataset
    _cache = Path(cache_path)
    p = Path(dataset_path)
    init_dataset(p, persist=True, cache_file=_cache)

    # w = Path(args.wds_path)
    # from pado_visualize.data.webdataset import init_wds
    # init_webdataset(w, persist=True, cache_file=_cache)


def init_app():
    from pado_visualize.routes import init_routes
    from pado_visualize.app import app

    # register all routes
    init_routes()

    # spawn app
    return app


def main():
    import argparse

    # parse commandline
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to a pado dataset")
    args = parser.parse_args()

    init_data(args.dataset_path, cache_path="./.pado_visualize.shelve")
    app = init_app()

    # run dev server
    app.run_server(host="127.0.0.1", port=8080, debug=True)


if __name__ == "__main__":
    main()
