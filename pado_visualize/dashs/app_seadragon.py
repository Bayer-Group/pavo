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
    output=Output("seadragon-script", "children"),
    inputs=[Input("url", "pathname")],
)
def view_slide(pathname):
    if not pathname.startswith("/slide/"):
        return ""
    slide_url = f"{pathname}/image.dzi"
    prefix_url = "/slide"
    return f"""
    $(document).ready(function() {{
        var viewer = new OpenSeadragon({{
            id: "seadragon-container",
            tileSources: "{slide_url}",
            prefixUrl: "{prefix_url}",
            showNavigator: true,
            showRotationControl: true,
            animationTime: 0.5,
            blendTime: 0.1,
            constrainDuringPan: true,
            maxZoomPixelRatio: 2,
            minZoomLevel: 1,
            visibilityRatio: 1,
            zoomPerScroll: 2,
            timeout: 120000,
        }});
        viewer.addHandler("open", function() {{
            // To improve load times, ignore the lowest-resolution Deep Zoom
            // levels.  This is a hack: we can't configure the minLevel via
            // OpenSeadragon configuration options when the viewer is created
            // from DZI XML.
            viewer.source.minLevel = 8;
        }});
    }});
    """


layout = html.Div([
    html.Div([], id="seadragon-container"),
    html.Script("", id="seadragon-script"),
])
