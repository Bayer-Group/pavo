from collections import defaultdict
from functools import lru_cache

import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

from pado.metadata import PadoColumn
from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset, get_metadata


@app.callback(
    output=Output("pado-table", "data"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ],
)
def render_table(pathname, data):
    df = get_metadata(filter_dict=data)
    if df is None:
        return []
    df = df.head(1000)
    return df.to_dict("records")


display_columns = [
    PadoColumn.STUDY.subcolumn("SHORT"),
    PadoColumn.EXPERIMENT,
    PadoColumn.GROUP,
    PadoColumn.ANIMAL,
    PadoColumn.COMPOUND,
    PadoColumn.ORGAN,
    PadoColumn.IMAGE.subcolumn("SHORT"),
    PadoColumn.FINDING,
    "annotation",
    "prediction"
]


layout = dbc.Row(
    dbc.Col(
        dbc.Card([
            dbc.CardHeader([
                "Metadata"
            ]),
            dbc.CardBody([
                dash_table.DataTable(
                    id='pado-table',
                    columns=[{"name": c.split("__")[0].upper(), "id": c} for c in display_columns],
                    style_as_list_view=True,
                    # style_header={
                    #    'backgroundColor': 'rgb(30, 30, 30)'
                    # },
                    # style_cell={
                    #    'backgroundColor': 'rgb(50, 50, 50)',
                    #    'color': 'white'
                    # },
                ),
            ])
        ], className="pado-card")
    )
)
