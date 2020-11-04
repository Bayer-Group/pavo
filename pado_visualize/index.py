import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pado_visualize.app import app
from pado_visualize.dashs import (
    app_landing,
    app_metadata,
    app_overview,
    app_project,
)
from pado_visualize.utils import rowcol

logo = html.Div([
    html.Div([
        html.Img(src=app.get_asset_url('pathological-heart.jpg')),
    ], className="logo-image-container"),
    html.Span("Pado", className="logo-text"),
    html.H3("Pathological Data Obsession", className="logo-subtext")
], className="pado-logo")

welcome_txt = html.P(
    "Welcome! Please select a display mode and the subset of data you want to look at."
)

nav_buttons = dbc.ButtonGroup(
    [
        dbc.Button("Graphs", href="/graphs", id="btn-graphs"),
        dbc.Button("Table", href="/table", id="btn-table"),
        dbc.Button("Slides", href="/slides", id="btn-slides")
    ],
    size="md",
    className="pado-nav-buttons",
),

sidebar = dbc.Container([
    rowcol(logo),
    rowcol(welcome_txt),
    dbc.Row(dbc.Col(nav_buttons)),
])

content = html.Div(id="page-content"),

# base layout of the landing page
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    dbc.Row([
        # add the sidebar of the landing page
        dbc.Col([sidebar], md=3, className="pado-sidebar"),
        # add the content
        dbc.Col(content, md=9, className="pado-content"),
    ], className="pado-body"),
], fluid=True)


@app.callback(
    output=Output("page-content", "children"),
    inputs=[Input("url", "pathname")],
)
def display_page(pathname):
    """update the index page dependent on the path"""
    if pathname == "/":
        return app_landing.layout
    elif pathname == "/graphs":
        return app_metadata.layout
    elif pathname == "/slides":
        return app_overview.layout
    elif pathname == "/slides":
        return app_project.layout
    else:
        return "404"


@app.callback(
    output=[
        Output(f"btn-{label}", "className")
        for label in ["graphs", "table", "slides"]
    ],
    inputs=[Input("url", "pathname")],
)
def set_active(pathname):
    return [
        "btn active" if pathname.startswith(f"/{label}") else "btn"
        for label in ["graphs", "table", "slides"]
    ]


