from pado_visualize.wsgi import init_data, init_app

def main():
    import argparse

    # parse commandline
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to a pado dataset")
    args = parser.parse_args()

    init_data(args.dataset_path, cache_path="./.pado_visualize.shelve")
    app = init_app()

    # run dev server
    app.run_server(host="127.0.0.1", port=8080, debug=False)


if __name__ == "__main__":
    main()
