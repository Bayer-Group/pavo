# import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from pado.ext.visualize.dataloader import get_dataset

layout = html.Div(
    [
        html.H1(children="Hello Dash"),
        html.Div(children="Dash: A web application framework for Python"),
    ]
)
