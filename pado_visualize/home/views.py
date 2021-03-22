from flask import Blueprint
from flask import render_template

# view blueprint for home endpoints
blueprint = Blueprint('home', __name__, url_prefix='/')


@blueprint.route("/")
@blueprint.route("/index.htm")
@blueprint.route("/index.html")
def index():
    return render_template("home/index.html", page_title="Home")
