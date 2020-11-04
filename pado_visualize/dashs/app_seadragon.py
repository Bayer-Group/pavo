# import dash
import itertools

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from flask import url_for
from dash.dependencies import Input, Output
from pado_visualize.app import app
from pado_visualize.dataloader import get_dataset


@app.callback(
    output=Output("seadragon-container", "data-tilesources"),
    inputs=[Input("url", "pathname")],
)
def view_slide(pathname):
    if not pathname.startswith("/slide/"):
        return ""
    slide_url = f"{pathname}/image.dzi"
    return slide_url


layout = html.Div([
    html.Div([], id="seadragon-container", **{"data-tilesources": ""}),
])
