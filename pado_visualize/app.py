"""dash instance submodule

to prevent circular imports provide Dash instance in its own submodule
"""
import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.SANDSTONE],
    suppress_callback_exceptions=True,
)
server = app.server
