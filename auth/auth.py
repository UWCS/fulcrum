import os
import secrets
from functools import wraps
from typing import Callable

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, Flask, abort, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.wrappers import Response

from schema import APIKey, db

oauth = OAuth()


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
    return any(role in session.get("groups", []) for role in ["exec", "sysadmin"])


def is_logged_in() -> bool:
    """Check if the user is logged in"""
    return "groups" in session and "id_token" in session


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login() -> Response:
    # redirect to keycloack for login
    redirect_uri = url_for("auth.auth", _external=True)
    return oauth.keycloak.authorize_redirect(redirect_uri)  # type: ignore


# callback route for keycloak to redirect to after login
@auth_bp.route("/auth")
def auth() -> Response:
    token = oauth.keycloak.authorize_access_token()  # type: ignore
    # save id token for logout
    session["id_token"] = token["id_token"]
    user = token["userinfo"]
    session["groups"] = user.get("groups", [])
    return redirect(url_for("index"))


@auth_bp.route("/logout")
def logout() -> Response:
    if "id_token" in session:
        # save token id for logout
        token_id = session["id_token"]
        session.clear()
        return redirect(
            "https://auth.uwcs.co.uk/realms/uwcs/protocol/openid-connect/logout"
            + f"?post_logout_redirect_uri{url_for('index', _external=True)}"
            + f"&id_token_hint={token_id}"
        )
    # if no id token, just clear session and redirect to index
    session.clear()
    return redirect(url_for("index"))


def create_api_key(owner: str) -> dict:
    """Create a new API key"""
    key = secrets.token_urlsafe(32)
    api_key = APIKey(generate_password_hash(key), owner.strip().lower())
    db.session.add(api_key)
    db.session.commit()
    return {
        "id": api_key.id,
        "key": key,
        "owner": api_key.owner,
        "active": api_key.active,
        "created_at": api_key.created_at.isoformat(),
    }


def get_api_keys() -> list[dict]:
    """Get all API keys"""
    api_keys = APIKey.query.all()
    return [key.to_dict() for key in api_keys]


def get_api_key(key_id: int) -> dict | None:
    """Get an API key by its ID"""
    api_key = APIKey.query.get(key_id)
    if not api_key:
        return None
    return api_key.to_dict()


def disable_api_key(key_id: int) -> dict | None:
    """Disable an API key by its ID"""
    api_key = APIKey.query.get(key_id)
    if not api_key:
        return None
    api_key.deactivate()
    return api_key.to_dict()


def is_valid_api_key(api_key: str) -> bool:
    """Check if an API key is valid"""
    for key in APIKey.query.filter_by(active=True).all():
        if check_password_hash(key.key, api_key):
            return True
    return False


def valid_api_auth(f: Callable) -> Callable:
    """decorater to check if valid API auth"""

    @wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> Response:
        # check if exec
        if is_exec():
            return f(*args, **kwargs)
        # check if valid API key
        # american spelling for convention
        api_key = request.headers.get("Authorization")
        if not api_key or not is_valid_api_key(api_key):
            return abort(403, "Invalid API key or not authorised.")
        return f(*args, **kwargs)

    return decorated_function


auth_api_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@auth_api_bp.route("/create", methods=["POST"])
@is_exec_wrapper
def create_api_key_api() -> tuple[Response, int]:
    """Create a new API key"""
    data = request.get_json()
    if not data or "owner" not in data:
        return jsonify({"error": "Owner is required"}), 400
    return jsonify(create_api_key(data["owner"])), 201


@auth_api_bp.route("/<int:key_id>", methods=["GET"])
@is_exec_wrapper
def get_api_key_api(key_id: int) -> tuple[Response, int]:
    """Get an API key by its ID"""
    api_key = get_api_key(key_id)
    if not api_key:
        return jsonify({"error": "API key not found"}), 404
    return jsonify(api_key), 200


@auth_api_bp.route("/disable/<int:key_id>", methods=["POST"])
@is_exec_wrapper
def disable_api_key_api(key_id: int) -> tuple[Response, int]:
    """Disable an API key by its ID"""
    api_key = disable_api_key(key_id)
    if not api_key:
        return jsonify({"error": "API key not found"}), 404
    return jsonify(api_key), 200


@auth_api_bp.route("/keys", methods=["GET"])
@is_exec_wrapper
def get_api_keys_api() -> tuple[Response, int]:
    """Get all API keys"""
    return jsonify(get_api_keys()), 200
