import secrets
from functools import wraps
from typing import Callable

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.wrappers import Response

from auth.oauth import is_exec, is_exec_wrapper
from schema import APIKey, db


def create_api_key(owner: str) -> dict:
    """Create a new API key"""
    key = secrets.token_urlsafe(32)
    api_key = APIKey(generate_password_hash(key), owner)
    db.session.add(api_key)
    db.session.commit()
    return {
        "id": api_key.id,
        "key": key,
        "owner": api_key.owner,
        "active": api_key.active,
        "created_at": api_key.created_at.isoformat(),
    }


def get_api_keys() -> list[APIKey]:
    """Get all API keys"""
    return APIKey.query.all()


def get_api_key(key_id: int) -> APIKey | None:
    """Get an API key by its ID"""
    return APIKey.query.get(key_id)


def deactivate_api_key(key_id: int) -> APIKey | None:
    """Deactivate an API key by its ID"""
    api_key = APIKey.query.get(key_id)
    if not api_key:
        return None
    api_key.deactivate()
    return api_key


def activate_api_key(key_id: int) -> APIKey | None:
    """Activate an API key by its ID"""
    api_key = APIKey.query.get(key_id)
    if not api_key:
        return None
    api_key.activate()
    return api_key


def delete_api_key(key_id: int) -> APIKey | None:
    """Delete an API key by its ID"""
    api_key = APIKey.query.get(key_id)
    if not api_key:
        return None
    db.session.delete(api_key)
    db.session.commit()
    return api_key


def is_valid_api_key(api_key: str) -> bool:
    """Check if an API key is valid"""
    for key in APIKey.query.filter_by(active=True).all():
        if check_password_hash(key.key_hash, api_key):
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
            return abort(
                403,
                "Invalid API key or not authorised. If you think this is a mistake, please contact a tech officer.",  # noqa: E501
            )
        return f(*args, **kwargs)

    return decorated_function


auth_api_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@auth_api_bp.route("/create", methods=["POST"])
@is_exec_wrapper
def create_api_key_api() -> tuple[Response, int]:
    """Create a new API key
    ---
    parameters:
      - name: owner
        in: body
        type: string
        description: Owner of the API key
        required: true
    responses:
        201:
            description: API key created successfully
            schema:
                $ref: '#/definitions/APIKey'
        400:
            description: Bad request, owner is required
        403:
            description: Forbidden.
    """
    data = request.get_json()
    if not data or "owner" not in data:
        return jsonify({"error": "Owner is required"}), 400
    return jsonify(create_api_key(data["owner"])), 201


@auth_api_bp.route("/<int:key_id>", methods=["GET"])
@is_exec_wrapper
def get_api_key_api(key_id: int) -> tuple[Response, int]:
    """Get an API key by its ID
    ---
    parameters:
      - in: path
        name: key_id
        type: integer
        required: true
        description: The ID of the API key to retrieve
    responses:
        200:
            description: API key retrieved successfully
            schema:
                $ref: '#/definitions/APIKey'
        404:
            description: API key not found
        403:
            description: Forbidden.
    """
    api_key = get_api_key(key_id)
    if not api_key:
        return jsonify({"error": "API key not found"}), 404
    return jsonify(api_key.to_dict()), 200


@auth_api_bp.route("/<int:key_id>/deactivate", methods=["POST"])
@is_exec_wrapper
def deactivate_api_key_api(key_id: int) -> tuple[Response, int]:
    """Deactivate an API key by its ID
    ---
    parameters:
      - in: path
        name: key_id
        type: integer
        required: true
        description: The ID of the API key to deactivate
    responses:
        200:
            description: API key deactivated successfully
            schema:
                $ref: '#/definitions/APIKey'
        404:
            description: API key not found
        403:
            description: Forbidden.
    """
    api_key = deactivate_api_key(key_id)
    if not api_key:
        return jsonify({"error": "API key not found"}), 404
    return jsonify(api_key.to_dict()), 200


@auth_api_bp.route("/<int:key_id>/activate", methods=["POST"])
@is_exec_wrapper
def activate_api_key_api(key_id: int) -> tuple[Response, int]:
    """Activate an API key by its ID
    ---
    parameters:
      - in: path
        name: key_id
        type: integer
        required: true
        description: The ID of the API key to activate
    responses:
        200:
            description: API key activated successfully
            schema:
                $ref: '#/definitions/APIKey'
        404:
            description: API key not found
        403:
            description: Forbidden.
    """
    api_key = activate_api_key(key_id)
    if not api_key:
        return jsonify({"error": "API key not found"}), 404
    return jsonify(api_key.to_dict()), 200


@auth_api_bp.route("/<int:key_id>/delete", methods=["DELETE"])
@is_exec_wrapper
def delete_api_key_api(key_id: int) -> tuple[Response, int]:
    """Delete an API key by its ID
    ---
    parameters:
      - in: path
        name: key_id
        type: integer
        required: true
        description: The ID of the API key to delete
    responses:
        200:
            description: API key deleted successfully
            schema:
                $ref: '#/definitions/APIKey'
        404:
            description: API key not found
        403:
            description: Forbidden.
    """
    api_key = delete_api_key(key_id)
    if not api_key:
        return jsonify({"error": "API key not found"}), 404
    return jsonify(api_key.to_dict()), 200


@auth_api_bp.route("/keys", methods=["GET"])
@is_exec_wrapper
def get_api_keys_api() -> tuple[Response, int]:
    """Get all API keys
    ---
    responses:
        200:
            description: List of all API keys
            schema:
                type: array
                items:
                    $ref: '#/definitions/APIKey'
        403:
            description: Forbidden.
    """
    keys = get_api_keys()
    return jsonify([key.to_dict() for key in keys]), 200


auth_ui_bp = Blueprint("auth_ui", __name__, url_prefix="/auth")


@auth_ui_bp.route("/keys", methods=["GET"])
@is_exec_wrapper
def get_api_keys_ui() -> str:
    return render_template("auth/keys.html", keys=get_api_keys())


@auth_ui_bp.route("/keys/create", methods=["POST"])
@is_exec_wrapper
def create_api_key_ui() -> Response:
    owner = request.form.get("owner")
    if not owner:
        flash("Owner is required", "error")
        return redirect(url_for("auth_ui.get_api_keys_ui"))

    api_key = create_api_key(owner)
    flash(f"API key for {owner}, created successfully!", "success")
    flash(f"Key: {api_key['key']}", "success")
    return redirect(url_for("auth_ui.get_api_keys_ui"))


def handle_api_key_action(
    action: Callable[[int], APIKey | None], verb: str
) -> Response:
    key_id = request.form.get("id")
    if not key_id:
        flash("API key ID is required", "error")
        return redirect(url_for("auth_ui.get_api_keys_ui"))

    api_key = action(int(key_id))
    if api_key is None:
        flash("API key not found", "error")
        return redirect(url_for("auth_ui.get_api_keys_ui"))

    flash(f"API key {api_key.id} {verb} successfully!", "info")
    return redirect(url_for("auth_ui.get_api_keys_ui"))


@auth_ui_bp.route("/keys/delete", methods=["POST"])
@is_exec_wrapper
def delete_api_key_ui() -> Response:
    return handle_api_key_action(delete_api_key, "deleted")


@auth_ui_bp.route("/keys/deactivate", methods=["POST"])
@is_exec_wrapper
def deactivate_api_key_ui() -> Response:
    return handle_api_key_action(deactivate_api_key, "deactivated")


@auth_ui_bp.route("/keys/activate", methods=["POST"])
@is_exec_wrapper
def activate_api_key_ui() -> Response:
    return handle_api_key_action(activate_api_key, "activated")
