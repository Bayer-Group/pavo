import dash_bootstrap_components as dbc


def rowcol(*children, **kwargs):
    return dbc.Row(dbc.Col(list(children)))
