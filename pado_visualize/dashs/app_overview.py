import itertools

import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output

from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset


@app.callback(
    output=Output("prev-card-container", "children"), inputs=[Input("url", "pathname")],
)
def render_preview_cards(pathname):
    ds = get_dataset(abort_if_none=True)
    cards = []
    for image_resource in itertools.islice(ds.images, 0, 100):
        img = html.Img(
            className="thumbnail", src=f"/thumbnails/{image_resource.id_str}.jpg"
        )
        overlay = html.Img(
            className="grid-overlay", src=f"/grid/{image_resource.id_str}.png"
        )
        # title = html.H5("Card title", className="card-title")
        card = html.A(
            [dbc.Card(
                [
                    # title,
                    img,
                    overlay,
                ],
                className="thumbnail-card",
            )], href=f"/slide/{image_resource.id_str}"
        )
        cards.append(card)
    return cards


layout = dbc.Row(
    dbc.Col(html.Div(id="prev-card-container", className="thumbnail-container"))
)
