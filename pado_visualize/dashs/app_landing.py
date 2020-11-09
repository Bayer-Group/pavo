import dash_bootstrap_components as dbc
import dash_html_components as html

# from pado.ext.visualize.app import app
from pado_visualize.dash_pado_components import RowCol

layout = dbc.Container(
    RowCol([
        dbc.Jumbotron(
            [
                html.P(
                    "Explore the metadata, image data, annotations and predictions stored in your PadoDataset.",
                ),
            ],
            className="pado-jumbotron",
        )
    ]),
    id="landing-container"
)

layout_404 = dbc.Container(
    RowCol([
        dbc.Jumbotron(
            [
                html.H1("404"),
                html.P("page or resource not found."),
            ],
            className="pado-jumbotron",
        )
    ]),
    id="error-container"
)
