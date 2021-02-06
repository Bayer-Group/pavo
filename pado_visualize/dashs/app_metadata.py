from urllib.parse import urlparse

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash import dash
from dash.dependencies import Input, Output

from pado.metadata import PadoColumn
from pado_visualize.app import app
from pado_visualize.components import PlotCard, InfoCard, RowCol, LabeledDropDown
from pado_visualize.data.dataset import get_metadata


def _plot_card_bar(x, y, title=None):
    # return px.bar(counts)
    bar_data = [go.Bar(x=x, y=y, marker_color="#ee99d4")]
    bar_layout = go.Layout(
        {
            "title": title,
            "yaxis": {},
            "xaxis": {
                "showticklabels": False
            },
            "height": 200,
            "margin": go.layout.Margin(l=0, r=0, t=0, b=0),
            "showlegend": False,
        }
    )
    fig = go.Figure(data=bar_data, layout=bar_layout)
    fig.update_layout(clickmode='event+select')
    return fig


layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            InfoCard(
                info_id="info-datasource",
                value="... slides",
                text="Number of slides in data sources",
            ),
        ], xs=4),
        dbc.Col([
            InfoCard(
                info_id="info-organs",
                value="... organ types",
                text="Number of types of organs in data source",
            ),
        ], xs=4),
        dbc.Col([
            InfoCard(
                info_id="info-annotations",
                value="... annotated",
                text="Annotated slides in data source",
            ),
        ], xs=4)
    ]),
    dbc.Row([
        dbc.Col([
            PlotCard(
                figure_id="fig-studies",
                title="Studies",
                text="Slides per study in dataset",
            ),
        ], xs=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([], id="selected-study-container")
        ], xs=12),
    ]),
    dbc.Row([
        dbc.Col([
            PlotCard(
                figure_id="fig-findings",
                title="Findings",
                text="Slides with findings in dataset",
            ),
        ], xs=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([], id="selected-finding-container")
        ], xs=12)
    ]),
])


@app.callback(
    output=Output("info-datasource", "children"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_info_datasource(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df[PadoColumn.IMAGE].unique().size
    return f"{counts} slides"


@app.callback(
    output=Output("info-organs", "children"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_info_organs(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df[PadoColumn.ORGAN].unique().size
    return f"{counts} organ types"


@app.callback(
    output=Output("info-annotations", "children"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_barchart_annotations(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df.loc[df["annotation"] == "true", PadoColumn.IMAGE].unique().size
    return f"{counts} annotated"


@app.callback(
    output=Output("fig-studies", "figure"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_barchart_studies(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df[PadoColumn.STUDY].value_counts()
    return _plot_card_bar(x=counts.index, y=counts.values)


@app.callback(
    output=Output("fig-findings", "figure"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ]
)
def update_barchart_findings(pathname, data):
    df = get_metadata(filter_dict=data)
    counts = df[PadoColumn.FINDING].value_counts()
    try:
        del counts["UNREMARKABLE"]
    except KeyError:
        pass
    return _plot_card_bar(x=counts.index[:20], y=counts.values[:20])


def _plot_summary_studies(df):
    title = "Selected Study Summary"
    selection = ", ".join(df["STUDY"].unique())
    text = f"Studies: {selection}"

    bar_data = []
    doses = (
        df[
            ["GROUP__DOSE", "GROUP__DOSE_UNIT"]
        ].set_index(
            df["GROUP__DOSE"]
        ).apply(
            lambda row: ' '.join(row.values.astype(str)), axis=1
        ).drop_duplicates(
        ).sort_index()
    )
    for finding, _df in df.groupby("FINDING")["GROUP__DOSE"]:
        if finding == "UNREMARKABLE":
            continue
        data = _df.value_counts().sort_index(ascending=True)
        cnts = []
        for d in doses.index:
            try:
                v = data[d]
            except KeyError:
                v = 0
            cnts.append(v)

        bar_data.append(
            go.Bar(name=finding, x=doses, y=cnts)
        )

    if not bar_data:
        return ""

    bar_layout = go.Layout(
        {
            "yaxis": {},
            "xaxis": {
                "showticklabels": True
            },
            "height": 320,
            "margin": go.layout.Margin(l=0, r=0, t=0.2, b=0),
            "showlegend": True,
            "legend": {'orientation': "h", 'yanchor': "bottom", 'y': 1.05, 'xanchor': "center", 'x': 0.5}
        }
    )
    fig = go.Figure(data=bar_data, layout=bar_layout)

    graph = dcc.Graph(figure=fig)
    content = [
        dbc.CardHeader([
            html.H5(title, className="card-title"),
        ]),
        dbc.CardBody([graph]),
        dbc.CardFooter([
            html.P(text, className="card-text"),
        ]),
    ]
    return dbc.Card(content, className="plot-card summary")


def _plot_summary_findings(df):
    title = "Selected Finding Summary"
    selection = ", ".join(df["FINDING"].unique())
    text = f"Findings: {selection}"

    bar_data = []
    for compound, _df in df.groupby("COMPOUND")["GROUP__DOSE_LEVEL"]:
        data = _df.value_counts().sort_index(ascending=True)
        bar_data.append(
            go.Bar(name=compound, x=data.index, y=data)
        )

    if not bar_data:
        return ""

    bar_layout = go.Layout(
        {
            "yaxis": {},
            "xaxis": {
                "showticklabels": True
            },
            "height": 320,
            "margin": go.layout.Margin(l=0, r=0, t=0.2, b=0),
            "showlegend": True,
            "legend": {'orientation': "h", 'yanchor': "bottom", 'y': 1.05, 'xanchor': "center", 'x': 0.5}
        }
    )
    fig = go.Figure(data=bar_data, layout=bar_layout)

    graph = dcc.Graph(figure=fig)
    content = [
        dbc.CardHeader([
            html.H5(title, className="card-title"),
        ]),
        dbc.CardBody([graph]),
        dbc.CardFooter([
            html.P(text, className="card-text"),
        ]),
    ]
    return dbc.Card(content, className="plot-card summary")


@app.callback(
    output=Output("selected-finding-container", "children"),
    inputs=[
        Input("fig-findings", "selectedData"),
        Input("subset-filter-store", "data"),
    ],
)
def display_selected_finding_data(selectedData, data):
    if not selectedData:
        return ""

    selected_findings = [pt.get("label") for pt in selectedData.get("points", [])]
    selected_findings = [f for f in selected_findings if f]

    if not selected_findings:
        return ""

    data.setdefault("FINDING", []).extend(selected_findings)
    df = get_metadata(filter_dict=data)
    return _plot_summary_findings(df)


@app.callback(
    output=Output("selected-study-container", "children"),
    inputs=[
        Input("fig-studies", "selectedData"),
        Input("subset-filter-store", "data"),
    ],
)
def display_selected_study_data(selectedData, data):
    if not selectedData:
        return ""

    selected_studies = [pt.get("label") for pt in selectedData.get("points", [])]
    selected_studies = [f for f in selected_studies if f]

    if not selected_studies:
        return ""

    data.setdefault("STUDY", []).extend(selected_studies)
    df = get_metadata(filter_dict=data)
    return _plot_summary_studies(df)


@app.callback(
    output=Output("slide-metadata-view", "children"),
    inputs=[
        Input("url", "pathname"),
    ],
    state=[
        Input("subset-filter-store", "data"),
    ],
)
def display_selected_study_data(pathname, data):
    from pado.images import ImageId
    result = urlparse(pathname)
    section, *subsection = result.path[1:].split("/")

    if section != "slide":
        return dash.no_update

    image_id = subsection[1]
    df = get_metadata(filter_dict=data)
    metadata = df.loc[df["IMAGE"] == "__".join(image_id)].T
    raise Exception("")
    if metadata.size == 0:
        metadata = df.loc[df["IMAGE"] == "__".join(ImageId.from_str(image_id))].T
    out = [
        RowCol(
            [
                html.Label(
                    [
                        label,
                        html.P(
                            value[0],
                            style={"margin": 0, "font-weight": 300}
                        )
                    ],
                    style={"font-weight": 800},
                )
            ],
            xs=12
        )
        for label, *value in metadata.itertuples() if ((not label.startswith("_")) and value)
    ]
    return out
