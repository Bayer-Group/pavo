import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pado.ext.visualize import app_landing, app_metadata, app_overview
from pado.ext.visualize.app import app

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
    else:
        return "404"


if __name__ == "__main__":
    import argparse

    from pado.ext.visualize.dataloader import set_dataset

    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_path", help="path to a pado dataset")
    args = parser.parse_args()
    set_dataset(args.dataset_path)

    app.run_server(debug=True)
