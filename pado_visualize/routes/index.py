import string

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pado.metadata import PadoReserved, PadoColumn

from pado_visualize.app import app
from pado_visualize.dashs import (
    app_landing,
    app_metadata,
    app_slides,
    app_seadragon,
    app_table,
)
from pado_visualize.components import LabeledDropDown, RowCol
from pado_visualize.data.dataset import get_dataset_column_values


# -- sidebar header ---------------------------------------------------

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


# -- sidebar navigation -----------------------------------------------

nav_buttons = dbc.ButtonGroup(
    [
        dbc.Button("Graphs", href="/graphs", id="btn-graphs"),
        dbc.Button("Table", href="/table", id="btn-table"),
        dbc.Button("Slides", href="/slides", id="btn-slides")
    ],
    size="md",
    className="pado-nav-buttons",
)


# -- dataset filtering inputs -----------------------------------------

DATASET_FILTER_INPUT_CONFIG = [
    # label, column, is_multi_select
    ("Dataset", PadoReserved.DATA_SOURCE_ID, True),
    ("Study", PadoColumn.STUDY, True),
    ("Organ", PadoColumn.ORGAN, True),
    ("Finding", PadoColumn.FINDING, True),
    ("Annotation", "annotation", False),
    ("Prediction", "prediction", False),
]

DATASET_FILTER_INPUT_DEPENDENCY = {
    # should options of DATASET_FILTER_INPUT_CONFIG[`key`] depend on changes of others
    1: [0],
    2: [0, 1],
    3: [0, 1, 2],
}

dataset_filter_inputs = []
for label, column, is_multi_select in DATASET_FILTER_INPUT_CONFIG:
    assert set(label).issubset(string.ascii_letters)
    dataset_filter_inputs.append(
        RowCol(
            [
                LabeledDropDown(
                    label,
                    id=f"data-{label.lower()}-select",
                    options=get_dataset_column_values(column),
                    multi=is_multi_select
                ),
            ],
            xs=12
        )
    )


# -- sidebar ----------------------------------------------------------

sidebar = dbc.Container(
    [
        RowCol([
            html.A([logo], href="/")
        ]),
        RowCol([welcome_txt]),
        html.H5("Display Mode"),
        RowCol([nav_buttons], style={"margin-bottom": "15px"}),
        html.H5("Subset Filter"),
        dbc.Form(children=dataset_filter_inputs),
    ],
    className="dash-bootstrap"
)


# -- page layout ------------------------------------------------------

content = html.Div(id="page-content")

# base layout of the landing page
app.layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        dbc.Row(
            [
                # add the sidebar of the landing page
                dbc.Col([sidebar], lg=3, className="pado-sidebar"),
                # add the content
                dbc.Col([content], lg=9, className="pado-content"),
            ],
            className="pado-body"
        ),
        dcc.Store(id='subset-filter-store', storage_type='session'),
    ],
    id="pado-body",
    fluid=True
)


# -- callbacks --------------------------------------------------------

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
        return app_slides.layout, ""
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


@app.callback(
    output=Output("subset-filter-store", "data"),
    inputs=[
        Input(f"data-{label.lower()}-select", "value")
        for label, _, _ in DATASET_FILTER_INPUT_CONFIG
    ]
)
def filter_dataset(*values):
    output = {}
    for (_, column, multi), val in zip(DATASET_FILTER_INPUT_CONFIG, values):
        if val is None and multi:
            val = []
        elif not multi and val is not None:
            val = [val]
        elif not multi and val is None:
            val = []
        output[column] = list(map(str, val))
    return output


# -- generated callbacks ----------------------------------------------

for idx, dep_idxs in DATASET_FILTER_INPUT_DEPENDENCY.items():

    label, column, _ = DATASET_FILTER_INPUT_CONFIG[idx]
    output_select = Output(f"data-{label.lower()}-select", "options")

    _columns = []
    for dep_idx in dep_idxs:
        _, filter_column, _ = DATASET_FILTER_INPUT_CONFIG[dep_idx]
        _columns.append(filter_column)

    @app.callback(
        output=output_select,
        inputs=[Input("subset-filter-store", "data")],
    )
    def options_filter(data, data_column=column, filter_columns=tuple(_columns)):
        filter_dict = {k: v for k, v in data.items() if k in filter_columns}
        return get_dataset_column_values(data_column, filter_dict=filter_dict)
