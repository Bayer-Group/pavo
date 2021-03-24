import functools
from flask import current_app
from flask import redirect
from flask import url_for
from flask_dance.contrib.azure import azure


def login_required(endpoint):
    @functools.wraps
    def _endpoint(*args, **kwargs):
        if current_app.config.OAUTH == "azure":
            if not azure.authorized:
                return redirect(url_for("azure.login"))
        return endpoint(*args, **kwargs)
    return _endpoint
