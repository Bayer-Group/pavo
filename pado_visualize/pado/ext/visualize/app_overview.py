# import dash
import itertools

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
from pado.ext.visualize.app import app
from pado.ext.visualize.dataloader import get_dataset


@app.callback(
    output=Output("preview-card-container", "children"),
    inputs=[Input("url", "pathname")],
)
def render_preview_cards(pathname):
    ds = get_dataset()
    cards = []
    for image_resource in itertools.islice(ds.images, 0, 100):
        img = html.Img(
            width="200", height="200", src=f"/thumbnails/{image_resource.id_str}.jpg"
        )
        card = dbc.Card([img])
        cards.append(card)
    return cards


layout = dbc.Row([html.Div(id="preview-card-container", children=[],)])
