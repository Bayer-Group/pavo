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

