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
