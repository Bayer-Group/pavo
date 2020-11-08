
def main():
    import argparse
    from pathlib import Path

    from pado_visualize.routes import init_routes
    from pado_visualize.data.dataset import init_dataset
    # from pado_visualize.data.webdataset import init_wds
    from pado_visualize.app import app

    # register all routes
    init_routes()

    parser = argparse.ArgumentParser()
    # parser.add_argument("--wds-path", help="path to wds path folder")
    parser.add_argument("dataset_path", help="path to a pado dataset")
    args = parser.parse_args()

    # dataset
    _cache = Path("./.pado_visualize.shelve")
    p = Path(args.dataset_path)
    init_dataset(p, persist=True, cache_file=_cache)
    # w = Path(args.wds_path)
    # init_webdataset(w, persist=True, cache_file=_cache)

    app.run_server(host="127.0.0.1", port=8080, debug=True)


if __name__ == "__main__":
    main()
