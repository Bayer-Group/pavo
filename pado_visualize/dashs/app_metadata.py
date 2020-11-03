# import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from pado_visualize.app import app
from pado_visualize.dataloader import get_dataset
from pado.metadata import PadoColumn, PadoReserved

record_cache = None


@app.callback(
    output=Output("metadata-container", "children"), inputs=[Input("url", "pathname")],
)
def render_preview_cards(pathname):
    global record_cache
    if record_cache is None:
        ds = get_dataset()
        record_cache = ds.metadata.to_dict("records"), ds.metadata.columns
    records, columns = record_cache
    table = dash_table.DataTable(
        id="table-virtualization",
        data=records,
        filter_action="native",
        columns=[{"name": i, "id": i} for i in columns],
        fixed_rows={"headers": True, "data": 0},
        style_cell={"whiteSpace": "normal"},
        style_data_conditional=[],
        virtualization=True,
        page_action="none",
    )
    return table


def plot_card(figure_id, title, text) -> dbc.Col:
    graph = dcc.Graph(id=figure_id, figure={},)
    content = [
        dbc.CardHeader(graph),
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                html.P(text, className="card-text"),
            ]
        ),
    ]
    card = dbc.Card(content, className="plot-card")
    column = dbc.Col(card, xs=12, sm=6, md=4, lg=3, xl=2)
    return column


def _plot_card_bar(x, y, title=None):
    # return px.bar(counts)
    bar_data = [go.Bar(x=x, y=y)]
    bar_layout = go.Layout(
        {
            "title": title,
            "yaxis": {},
            "xaxis": {},
            "height": 200,
            "margin": go.layout.Margin(l=0, r=0, t=0, b=0),
            "showlegend": False,
        }
    )
    return go.Figure(data=bar_data, layout=bar_layout)


layout = dbc.Container(
    dbc.Row(
        [
            plot_card(
                figure_id="fig-datasource",
                title="Data sources",
                text="Slides per data sources contained in dataset",
            ),
            plot_card(
                figure_id="fig-studies",
                title="Studies",
                text="Slides per study in dataset",
            ),
            plot_card(
                figure_id="fig-organs",
                title="Organs",
                text="Slides per organ in dataset",
            ),
            plot_card(
                figure_id="fig-annotations",
                title="Annotations",
                text="Annotated slides in dataset",
            ),
            plot_card(
                figure_id="fig-findings",
                title="Findings",
                text="Slides with findings in dataset",
            ),
        ]
    ),
    fluid=True,
)


@app.callback(
    output=Output("fig-datasource", "figure"), inputs=[Input("url", "pathname")]
)
def update_barchart_datasource(pathname):
    ds = get_dataset()
    counts = ds.metadata[PadoReserved.DATA_SOURCE_ID].value_counts()
    return _plot_card_bar(x=counts.index, y=counts.values,)


@app.callback(output=Output("fig-studies", "figure"), inputs=[Input("url", "pathname")])
def update_barchart_studies(pathname):
    ds = get_dataset()
    counts = ds.metadata[PadoColumn.STUDY].value_counts()
    return _plot_card_bar(x=counts.index, y=counts.values,)


@app.callback(output=Output("fig-organs", "figure"), inputs=[Input("url", "pathname")])
def update_barchart_organs(pathname):
    ds = get_dataset()
    counts = ds.metadata[PadoColumn.ORGAN].value_counts()
    return _plot_card_bar(x=counts.index, y=counts.values,)


@app.callback(
    output=Output("fig-annotations", "figure"), inputs=[Input("url", "pathname")]
)
def update_barchart_annotations(pathname):
    ds = get_dataset()
    counts = (
        ds.metadata[PadoColumn.IMAGE].map(ds.annotations.__contains__).value_counts()
    )
    return _plot_card_bar(x=counts.index, y=counts.values,)


@app.callback(
    output=Output("fig-findings", "figure"), inputs=[Input("url", "pathname")]
)
def update_barchart_findings(pathname):
    ds = get_dataset()
    counts = ds.metadata[PadoColumn.FINDING].value_counts()
    return _plot_card_bar(x=counts.index[:20], y=counts.values[:20],)
