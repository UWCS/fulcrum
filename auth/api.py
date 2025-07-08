import secrets
from functools import wraps
from typing import Callable

from flask import Blueprint, abort, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.wrappers import Response

from auth.oauth import is_exec, is_exec_wrapper
from schema import APIKey, db

auth_api_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


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
            return abort(
                403,
                "Invalid API key or not authorised. If you think this is a mistake, please contact a tech officer.",  # noqa: E501
            )
        return f(*args, **kwargs)

    return decorated_function


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
    return jsonify(api_key), 200


@auth_api_bp.route("/disable/<int:key_id>", methods=["POST"])
@is_exec_wrapper
def disable_api_key_api(key_id: int) -> tuple[Response, int]:
    """Disable an API key by its ID
    ---
    parameters:
      - in: path
        name: key_id
        type: integer
        required: true
        description: The ID of the API key to disable
    responses:
        200:
            description: API key disabled successfully
            schema:
                $ref: '#/definitions/APIKey'
        404:
            description: API key not found
        403:
            description: Forbidden.
    """
    api_key = disable_api_key(key_id)
    if not api_key:
        return jsonify({"error": "API key not found"}), 404
    return jsonify(api_key), 200


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
    return jsonify(get_api_keys()), 200
