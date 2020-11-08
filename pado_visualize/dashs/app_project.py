import dash_bootstrap_components as dbc
import dash_table
from dash.dependencies import Input, Output

from pado.metadata import PadoColumn
from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset


@app.callback(
    output=Output("pado-table", "data"),
    inputs=[Input("url", "pathname")],
)
def render_table(pathname):
    ds = get_dataset(abort_if_none=True)
    return ds.metadata.to_dict("records")


layout = dbc.Row(
    dbc.Col(
        dash_table.DataTable(
            id='pado-table',
            columns=[{"name": c, "id": c} for c in PadoColumn],
            style_as_list_view=True,
            style_header={'backgroundColor': 'rgb(30, 30, 30)'},
            style_cell={
                'backgroundColor': 'rgb(50, 50, 50)',
                'color': 'white'
            },
        ),
    )
)
