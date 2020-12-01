import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


def RowCol(children, **col_kwargs) -> dbc.Row:
    return dbc.Row(dbc.Col(children, **col_kwargs))


def LabeledDropDown(label, /, *args, **kwargs) -> html.Label:
    multi = kwargs.pop("multi", True)  # default to multi select
    return html.Label(
        [label, dcc.Dropdown(*args, multi=multi, **kwargs)],
    )


def PlotCard(figure_id, title, text) -> dbc.Card:
    graph = dcc.Graph(id=figure_id, figure={})
    content = [
        dbc.CardHeader([
            html.H5(title, className="card-title"),
        ]),
        dbc.CardBody([graph]),
        dbc.CardFooter([
            html.P(text, className="card-text"),
        ]),
    ]
    return dbc.Card(content, className="plot-card")


def InfoCard(info_id, value, text) -> dbc.Card:
    return dbc.Card([
        dbc.CardBody([
            html.H5(value, className="card-title", id=info_id),
            html.P(text, className="card-text"),
        ])
    ], className="info-card")
