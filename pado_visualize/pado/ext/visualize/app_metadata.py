# import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from pado.ext.visualize.dataloader import get_dataset

# fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

layout = html.Div(
    [
        html.H1(children="Hello Dash"),
        html.Div(children="Dash: A web application framework for Python"),
        # dcc.Graph(id="example-graph", figure=fig),
    ]
)
