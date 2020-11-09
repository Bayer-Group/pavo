import itertools

import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output

from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset, filter_metadata


@app.callback(
    output=Output("prev-card-container", "children"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ],
)
def render_preview_cards(pathname, data):
    ds = get_dataset(abort_if_none=True)

    df = filter_metadata(ds.metadata, filter_items=data)
    image_ids = df["IMAGE"].unique()

    cards = []
    for image_resource in ds.images:
        if image_resource.id_str not in image_ids:
            continue
        if not image_resource.local_path.is_file():
            continue
        img = html.Img(
            className="thumbnail", src=f"/thumbnails/slide_{image_resource.id_str}.jpg"
        )
        overlay = html.Img(
            className="grid-overlay", src=f"/thumbnails/tiling_{image_resource.id_str}.jpg"
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
        if len(cards) >= 100:
            break
    print("Got:", len(cards), "thumbnails")
    return cards


layout = dbc.Row(
    dbc.Col(html.Div(id="prev-card-container", className="thumbnail-container"))
)
