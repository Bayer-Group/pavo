"""pado_visualize.oauth

basis for flask danced backed authentication

!! This is currently not used. Handling the authentication via oidc
!! was an initial requirement for deployment but has now moved to the
!! end of the priority queue. This will become interesting once we
!! decide to include more user features.

"""
from __future__ import annotations

import functools
from typing import Optional

from flask import Blueprint
from flask import Flask
from flask import current_app
from flask import redirect
from flask import url_for

try:
    from flask_dance.contrib import azure
except ImportError:
    azure = None


def make_blueprint(app: Flask) -> Optional[Blueprint]:
    """create the oauth blueprint via flask-dance"""
    provider = app.config.OAUTH_PROVIDER
    if not provider or provider == "none":
        return None

    elif provider == "azure":
        # noinspection PyUnresolvedReferences
        return azure.make_azure_blueprint(
            client_id=app.config.OAUTH_AZURE_CLIENT_ID,
            client_secret=app.config.OAUTH_AZURE_CLIENT_SECRET,
            scope=app.config.OAUTH_AZURE_SCOPE,
            tenant=app.config.OAUTH_AZURE_TENANT_ID,
            redirect_to='home.index',
        )

    else:
        raise ValueError(f"unsupported oauth provider {provider!r}")


def login_required(endpoint):
    """simple login decorator"""
    # noinspection PyUnresolvedReferences
    @functools.wraps(endpoint)
    def _endpoint(*args, **kwargs):
        provider = current_app.config.OAUTH_PROVIDER
        if provider == "azure":
            oidc_proxy = azure.azure
        else:
            return endpoint(*args, **kwargs)

        if not oidc_proxy.authorized:
            return redirect(url_for("azure.login"))
        return endpoint(*args, **kwargs)
    return _endpoint
