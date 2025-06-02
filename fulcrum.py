import os
from pathlib import Path
from typing import Any

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session, url_for
from werkzeug.wrappers import Response

# if .env file exists, load it
if Path(".env").exists():
    load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

oath = OAuth(app)
oath.register(
    name="keycloak",
    client_id="events",
    client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET"),
    server_metadata_url="https://auth.uwcs.co.uk/realms/uwcs/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid profile groups",
        "token_endpoint_auth_method": "client_secret_post",
    },
)


@app.route("/")
def index() -> str:
    return render_template(
        "index.html", name=session.get("name"), groups=session.get("groups")
    )


@app.route("/login")
def login() -> Any:  # noqa: ANN401
    redirect_uri = url_for("auth", _external=True)
    return oath.keycloak.authorize_redirect(redirect_uri)  # type: ignore


@app.route("/auth")
def auth() -> Response:
    token = oath.keycloak.authorize_access_token()  # type: ignore
    user = token["userinfo"]  # type: ignore
    session["name"] = user.get("name", "Unknown")
    session["groups"] = user.get("groups", [])
    return redirect(url_for("index"))


@app.route("/logout")
def logout() -> Response:
    session.clear()
    return redirect(
        "https://auth.uwcs.co.uk/realms/uwcs/protocol/openid-connect/logout?redirect_uri="
        + url_for("index", _external=True)
    )
