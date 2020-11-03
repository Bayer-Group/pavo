import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pado_visualize.app import app
from pado_visualize.dashs import (
    app_landing,
    app_metadata,
    app_overview,
    app_project,
)

# base layout of the landing page
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Home", href="/")),
                dbc.NavItem(dbc.NavLink("Metadata", href="/metadata")),
                dbc.NavItem(dbc.NavLink("Overview", href="/overview")),
            ],
            brand="Pado Dataset",
            brand_href="/",
            color="primary",
            dark=True,
        ),
        html.Div(id="page-content"),
    ]
)


@app.callback(
    output=Output("page-content", "children"), inputs=[Input("url", "pathname")],
)
def display_page(pathname):
    """update the index page dependent on the path"""
    if pathname == "/":
        return app_landing.layout
    elif pathname == "/metadata":
        return app_metadata.layout
    elif pathname == "/overview":
        return app_overview.layout
    elif pathname == "/project":
        return app_project.layout
    else:
        return "404"


def main():
    import argparse
    import shelve
    from pathlib import Path

    from pado.ext.visualize.dataloader import (
        get_wds_map,
        set_dataset,
        set_dataset_from_store,
        set_wds_dirs,
        set_wds_map_from_store,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--wds-path", help="path to wds path folder")
    parser.add_argument("dataset_path", help="path to a pado dataset")
    args = parser.parse_args()

    p = Path(args.dataset_path).expanduser().absolute().resolve()
    w = Path(args.wds_path).expanduser().absolute().resolve()

    with shelve.open(".pado_visualize.shelve") as store:
        if str(p) not in store:
            print("getting dataset")
            store[str(p)] = set_dataset(p)
        else:
            print("getting cached dataset")
            set_dataset_from_store(store[str(p)])

        if str(w) not in store:
            print("getting wds_map")
            store[str(w)] = set_wds_dirs(w)
        else:
            print("getting cached wds_map")
            set_wds_map_from_store(store[str(w)])

    app.run_server(host="127.0.0.1", port=8080, debug=True)


if __name__ == "__main__":
    main()
