import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

from pado.metadata import PadoColumn, PadoReserved
from pado_visualize.app import app
from pado_visualize.dash_pado_components import PlotCard, InfoCard
from pado_visualize.data.dataset import get_dataset, get_metadata

record_cache = None


def _plot_card_bar(x, y, title=None):
    # return px.bar(counts)
    bar_data = [go.Bar(x=x, y=y, marker_color="#ee99d4")]
    bar_layout = go.Layout(
        {
            "title": title,
            "yaxis": {},
            "xaxis": {
                "showticklabels": False
            },
            "height": 200,
            "margin": go.layout.Margin(l=0, r=0, t=0, b=0),
            "showlegend": False,
        }
    )
    return go.Figure(data=bar_data, layout=bar_layout)


layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            InfoCard(
                info_id="info-datasource",
                value="... slides",
                text="Number of slides in data sources",
            ),
        ], xs=4),
        dbc.Col([
            InfoCard(
                info_id="info-organs",
                value="... organ types",
                text="Number of types of organs in data source",
            ),
        ], xs=4),
        dbc.Col([
            InfoCard(
                info_id="info-annotations",
                value="... annotated",
                text="Annotated slides in data source",
            ),
        ], xs=4)
    ]),
    dbc.Row([
        dbc.Col([
            PlotCard(
                figure_id="fig-studies",
                title="Studies",
                text="Slides per study in dataset",
            ),
        ], xs=12)
    ]),
    dbc.Row([
        dbc.Col([
            PlotCard(
                figure_id="fig-findings",
                title="Findings",
                text="Slides with findings in dataset",
            ),
        ], xs=12)
    ]),
])


@app.callback(
    output=[
        Output("info-datasource", "children"),
    ],
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_info_datasource(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df[PadoReserved.DATA_SOURCE_ID].value_counts()
    return f"{sum(counts.values)} slides",


@app.callback(
    output=Output("info-organs", "children"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_info_organs(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df[PadoColumn.ORGAN].unique().size
    return f"{counts} organ types"


@app.callback(
    output=Output("info-annotations", "children"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_barchart_annotations(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = sum(df["annotation"] == "true")
    return f"{counts} annotated"


@app.callback(
    output=Output("fig-studies", "figure"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_barchart_studies(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df[PadoColumn.STUDY].value_counts()
    return _plot_card_bar(x=counts.index, y=counts.values)


@app.callback(
    output=Output("fig-findings", "figure"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_barchart_findings(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df[PadoColumn.FINDING].value_counts()
    return _plot_card_bar(x=counts.index[:20], y=counts.values[:20])
