import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from pado.ext.visualize.app import app
from pado.ext.visualize import app_metadata


# base layout of the landing page
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(
    output=Output('page-content', 'children'),
    inputs=[Input('url', 'pathname')],
)
def display_page(pathname):
    """update the index page dependent on the path"""
    if pathname == '/metadata':
        return app_metadata.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)
