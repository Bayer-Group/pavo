import functools
from flask import current_app
from flask import redirect
from flask import url_for
try:
    from flask_dance.contrib.azure import azure
except ImportError:
    azure = None


def login_required(endpoint):
    @functools.wraps(endpoint)
    def _endpoint(*args, **kwargs):
        if current_app.config.OAUTH_PROVIDER == "azure":
            if azure is None:
                raise ImportError("flask_dance can't be imported")
            if not azure.authorized:
                return redirect(url_for("azure.login"))
        return endpoint(*args, **kwargs)
    return _endpoint
