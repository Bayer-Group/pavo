import dash_html_components as html
from dash.dependencies import ClientsideFunction, Input, Output

from pado_visualize.app import app


app.clientside_callback(
    ClientsideFunction(
        namespace="clientside",
        function_name="load_open_seadragon_multi",
    ),
    output=Output("seadragon-multi-container", "data-tilesources"),
    inputs=[Input("url", "pathname")],
)


layout = html.Div([
    html.Div(
        [],
        id="seadragon-multi-container",
        className="openseadragon needsclick",
        **{"data-tilesources": ""}
    ),
], className="seadragon-container-parent")
