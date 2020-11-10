import itertools
import time

import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output

from pado_visualize.app import app
from pado_visualize.data.dataset import get_dataset, get_image_map, get_metadata


@app.callback(
    output=Output("prev-card-container", "children"),
    inputs=[
        Input("url", "pathname"),
        Input("subset-filter-store", "data"),
    ],
)
def render_preview_cards(pathname, data):
    start = time.time()
    df = get_metadata(filter_dict=data)
    image_ids = set(df["IMAGE"].unique())
    print("Got", "took", time.time() - start)
    im = get_image_map()

    cards = []
    for image_id_str in image_ids.intersection(im):
        p = get_image_map()[image_id_str]
        if not p or not p.is_file():
            continue

        # images
        img = html.Img(
            className="thumbnail", src=f"/thumbnails/slide_{image_id_str}.jpg"
        )
        overlay = html.Img(
            className="grid-overlay", src=f"/thumbnails/tiling_{image_id_str}.jpg"
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
            )], href=f"/slide/{image_id_str}"
        )
        cards.append(card)
        if len(cards) >= 100:
            break
    print("Got:", len(cards), "thumbnails", "took", time.time() - start)
    return cards


layout = dbc.Row(
    dbc.Col(html.Div(id="prev-card-container", className="thumbnail-container"))
)
