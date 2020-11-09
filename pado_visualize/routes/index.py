import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pado.metadata import PadoReserved, PadoColumn

from pado_visualize.app import app
from pado_visualize.dashs import (
    app_landing,
    app_metadata,
    app_overview,
    app_seadragon,
    app_table,
)
from pado_visualize.dash_pado_components import LabeledDropDown, RowCol
from pado_visualize.data.dataset import get_dataset_column_values

logo = html.Div([
    html.Div([
        html.Img(src=app.get_asset_url('pathological-heart.jpg')),
    ], className="logo-image-container"),
    html.Span("Pado", className="logo-text"),
    html.H3("Pathological Data Obsession", className="logo-subtext")
], className="pado-logo")

welcome_txt = html.P(
    "Welcome! Please select a display mode and the subset of data you want to look at."
)

nav_buttons = dbc.ButtonGroup(
    [
        dbc.Button("Graphs", href="/graphs", id="btn-graphs"),
        dbc.Button("Table", href="/table", id="btn-table"),
        dbc.Button("Slides", href="/slides", id="btn-slides")
    ],
    size="md",
    className="pado-nav-buttons",
),

sidebar = dbc.Container([
    RowCol([
        html.A([logo], href="/")
    ]),
    RowCol([welcome_txt]),
    html.H5("Display Mode"),
    RowCol(nav_buttons, style={"margin-bottom": "15px"}),
    html.H5("Subset Filter"),
    dbc.Form(
        children=[
            RowCol(
                [
                    LabeledDropDown(
                        "Dataset",
                        id="data-dataset-select",
                        options=get_dataset_column_values(PadoReserved.DATA_SOURCE_ID),
                    ),
                ],
                xs=12
            ),
            RowCol(
                [
                    LabeledDropDown(
                        "Studies",
                        id="data-study-select",
                        options=get_dataset_column_values(PadoColumn.STUDY),
                    ),
                ],
                xs=12
            ),
            RowCol(
                [
                    LabeledDropDown(
                        "Organs",
                        id="data-organ-select",
                        options=get_dataset_column_values(PadoColumn.ORGAN),
                    ),
                ],
                xs=12
            ),
            RowCol(
                [
                    LabeledDropDown(
                        "Findings",
                        id="data-finding-select",
                        options=get_dataset_column_values(PadoColumn.FINDING),
                    ),
                ],
                xs=12
            ),
            RowCol(
                [
                    LabeledDropDown(
                        "Annotations",
                        id="data-annotation-select",
                        options=get_dataset_column_values("annotations"),
                        multi=False,
                    ),
                ],
                xs=12
            ),
            RowCol(
                [
                    LabeledDropDown(
                        "Predictions",
                        id="data-prediction-select",
                        options=get_dataset_column_values("predictions"),
                        multi=False,
                    ),
                ],
                xs=12
            ),
        ],
    ),
], className="dash-bootstrap")

content = html.Div(id="page-content"),

# base layout of the landing page
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    dbc.Row([
        # add the sidebar of the landing page
        dbc.Col([sidebar], lg=3, className="pado-sidebar"),
        # add the content
        dbc.Col(content, lg=9, className="pado-content"),
    ], className="pado-body"),
    dcc.Store(id='subset-filter-store', storage_type='session'),
], id="pado-body", fluid=True)


@app.callback(
    output=[
        Output("page-content", "children"),
        Output("pado-body", "className"),
    ],
    inputs=[Input("url", "pathname")],
)
def display_page(pathname):
    """update the index page dependent on the path"""
    if pathname == "/":
        return app_landing.layout, "pado-background"
    elif pathname == "/graphs":
        return app_metadata.layout, ""
    elif pathname == "/slides":
        return app_overview.layout, ""
    elif pathname.startswith("/slide/"):
        return app_seadragon.layout, ""
    elif pathname == "/table":
        return app_table.layout, ""
    else:
        # 404
        return app_landing.layout_404, "pado-background"


@app.callback(
    output=[
        Output(f"btn-{label}", "className")
        for label in ["graphs", "table", "slides"]
    ],
    inputs=[Input("url", "pathname")],
)
def set_active(pathname):
    return [
        "btn active" if pathname.startswith(f"/{label}") else "btn"
        for label in ["graphs", "table", "slides"]
    ]


# keep in sync with layout
FILTER_INPUTS = [
    "dataset", "study", "organ", "finding", "annotation", "prediction"
]
COLUMN_NAMES = [
    PadoReserved.DATA_SOURCE_ID,
    PadoColumn.STUDY,
    PadoColumn.ORGAN,
    PadoColumn.FINDING,
    "annotation",
    "prediction",
]


@app.callback(
    output=Output("subset-filter-store", "data"),
    inputs=[
        Input(f"data-{column}-select", "value") for column in FILTER_INPUTS
    ]
)
def filter_dataset(*values):
    return tuple(zip(COLUMN_NAMES, values))
