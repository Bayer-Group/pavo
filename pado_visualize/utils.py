import dash_bootstrap_components as dbc


def rowcol(*children, **_):
    return dbc.Row(dbc.Col(list(children)))
