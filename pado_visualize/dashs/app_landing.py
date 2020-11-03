# import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px

# from pado.ext.visualize.app import app
from pado_visualize.utils import rowcol

layout = dbc.Container(
    rowcol(
        dbc.Jumbotron(
            [
                html.H1("Visualize your dataset", className="display-3"),
                html.P(
                    "pado let's you visualize the metadata, image data "
                    "and annotations in your PadoDataset.",
                    className="lead",
                ),
                html.P(dbc.Button("Open Dataset", color="primary"), className="lead"),
            ]
        )
    )
)
