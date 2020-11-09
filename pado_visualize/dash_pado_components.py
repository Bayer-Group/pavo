import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


def RowCol(children, **col_kwargs) -> dbc.Row:
    return dbc.Row(dbc.Col(children, **col_kwargs))


def LabeledDropDown(label, /, *args, **kwargs) -> html.Label:
    return html.Label(
        [label, dcc.Dropdown(*args, className="dash-bootstrap", **kwargs)],
    )
