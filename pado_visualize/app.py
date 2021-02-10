"""dash instance submodule"""
# prevent circular imports by providing Dash instance in its own submodule
import logging
import sys
from logging.config import dictConfig

import dash
import dash_bootstrap_components as dbc


# --- configure logging handlers as early as possible -----------------

dictConfig({
    'version': 1,
    'root': {
        'level': 'INFO',
    },
})

for logger_name in ['pado_visualize.data.dataset']:
    logger = logging.getLogger(logger_name)
    backend_handler = logging.StreamHandler(sys.stderr)
    backend_handler.setFormatter(
        logging.Formatter('%(name)s::%(levelname)s: %(message)s')
    )
    logger.addHandler(backend_handler)


# === instantiate application instance ================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.SANDSTONE],
    suppress_callback_exceptions=True,
)
server = app.server
