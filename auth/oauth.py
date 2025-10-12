import os
from functools import wraps
from typing import Callable

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, Flask, abort, redirect, request, session, url_for
from werkzeug.wrappers import Response

oauth = OAuth()

scheme = "https"


def configure_oauth(app: Flask) -> None:
    """initialise oauth"""
    oauth.init_app(app)
    oauth.register(
        name="keycloak",
        client_id="events",
        client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET", ""),
        server_metadata_url="https://auth.uwcs.co.uk/realms/uwcs/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid profile groups",
            "token_endpoint_auth_method": "client_secret_post",
        },
    )

    global scheme  # noqa: PLW0603
    scheme = "http" if app.debug else "https"


def is_exec_wrapper(f: Callable) -> Callable:
    """decorate to check if the user is authed and in exec or sysadmin group"""

    @wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> Response:
        if not is_logged_in():
            return abort(403, "You must be logged in to access this page.")
        if not is_exec():
            return abort(
                403,
                "You must be in the exec or sysadmin group to access this page. Speak to a tech officer if you think this is a mistake.",  # noqa: E501
            )
        return f(*args, **kwargs)

    return decorated_function


def is_exec() -> bool:
    """check if the user is in the exec or sysadmin group"""
    return (
        any(role in session.get("groups", []) for role in ["exec", "sysadmin"])
        or os.getenv("DEV") == "1"
    )


def is_logged_in() -> bool:
    """Check if the user is logged in"""
    return ("groups" in session and "id_token" in session) or os.getenv("DEV") == "1"


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login/")
def login() -> Response:
    # save next url to session for redirect after login
    session["next"] = request.args.get("next") or request.referrer or url_for("index")
    # redirect to keycloack for login
    redirect_uri = url_for("auth.auth", _external=True, _scheme=scheme)
    return oauth.keycloak.authorize_redirect(redirect_uri)  # type: ignore


# callback route for keycloak to redirect to after login
@auth_bp.route("/auth/")
def auth() -> Response:
    token = oauth.keycloak.authorize_access_token()  # type: ignore

    # save id token for logout
    session["id_token"] = token["id_token"]
    user = token["userinfo"]
    session["groups"] = user.get("groups", [])

    # redirect to next url or index
    return redirect(session.pop("next", url_for("index")))


@auth_bp.route("/logout/")
def logout() -> Response:
    if "id_token" in session:
        # save token id for logout
        id_token = session["id_token"]
        session.clear()
        return redirect(
            "https://auth.uwcs.co.uk/realms/uwcs/protocol/openid-connect/logout"
            + f"?post_logout_redirect_uri={url_for('index', _external=True, _scheme=scheme)}"
            + f"&id_token_hint={id_token}"
        )
    # if no id token, just clear session and redirect to index
    session.clear()
    return redirect(url_for("index"))
