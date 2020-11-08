
def main():
    import argparse
    import shelve
    from pathlib import Path

    from pado_visualize.routes import init_routes
    from pado_visualize.data.dataset import init_dataset
    from pado_visualize.dataloader import (
        get_wds_map,
        set_dataset,
        set_dataset_from_store,
        set_wds_dirs,
        set_wds_map_from_store,
    )
    from pado_visualize.app import app

    # register all routes
    init_routes()

    parser = argparse.ArgumentParser()
    # parser.add_argument("--wds-path", help="path to wds path folder")
    parser.add_argument("dataset_path", help="path to a pado dataset")
    args = parser.parse_args()

    p = Path(args.dataset_path).expanduser().absolute().resolve()
    # w = Path(args.wds_path).expanduser().absolute().resolve()

    init_dataset(p, persist=True)

        # if str(w) not in store:
        #     print("getting wds_map")
        #     # store[str(w)] = set_wds_dirs(w)
        # else:
        #     print("getting cached wds_map")
        #     # set_wds_map_from_store(store[str(w)])

    app.run_server(host="127.0.0.1", port=8080, debug=True)


if __name__ == "__main__":
    main()
