import json

from flask import Blueprint
from flask import render_template

from pado_visualize._auth import login_required

# view blueprint for home endpoints
blueprint = Blueprint('home', __name__)


@blueprint.route("/")
@blueprint.route("/index.htm")
@blueprint.route("/index.html")
@login_required
def index():
    return render_template("home/index.html", page_title="Home")


@blueprint.route("/health")
def health():
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
