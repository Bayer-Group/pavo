from pathlib import Path
from typing import List


def init_data(dataset_path: List[str], cache_path: str, rebuild: bool):
    from pado_visualize.data.dataset import (
        init_dataset,
        get_dataset,
        get_metadata,
        get_image_map,
        get_annotation_map,
    )

    # dataset
    _cache = Path(cache_path)
    p = [Path(d) for d in dataset_path]
    init_dataset(p, persist=True, cache_file=_cache, ignore_cache=rebuild)

    # w = Path(args.wds_path)
    # from pado_visualize.data.webdataset import init_wds
    # init_webdataset(w, persist=True, cache_file=_cache)

    # warm caches
    print("warming caches...", end=" ", flush=True)
    get_dataset()
    get_image_map()
    get_metadata(filter_dict={})
    get_annotation_map()
    print("OK")


def init_app():
    from pado_visualize.routes import init_routes
    from pado_visualize.app import app

    # register all routes
    init_routes()

    # spawn app
    return app

