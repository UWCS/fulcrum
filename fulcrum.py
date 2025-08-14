import os
from json import load
from pathlib import Path

from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, redirect, render_template, request
from werkzeug.routing import IntegerConverter
from werkzeug.wrappers import Response

from auth.api import auth_api_bp, auth_ui_bp
from auth.oauth import auth_bp, configure_oauth, is_exec, is_logged_in
from config import colours
from events.api import events_api_bp
from events.ui import events_ui_bp
from events.utils import get_previous_events, get_upcoming_events, group_events
from schema import initialise_db

# if .env file exists, load it
if Path(".env").exists():
    load_dotenv()

# initialise flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# allow for use of signed ints in routes
class SignedIntConverter(IntegerConverter):
    regex = r"-?\d+"


app.url_map.converters["sint"] = SignedIntConverter

# initialise database
initialise_db(app)

# setup oauth and add routes
configure_oauth(app)
app.register_blueprint(auth_bp, url_prefix="/")
app.register_blueprint(auth_ui_bp, url_prefix="/auth")

# add api routes
app.register_blueprint(events_api_bp, url_prefix="/api/events")
app.register_blueprint(auth_api_bp, url_prefix="/api/auth")

# setup Swagger
with Path("swagger.json").open("r") as f:
    swagger = Swagger(app, template=load(f))


# add event ui routes
app.register_blueprint(events_ui_bp, url_prefix="/")


# context processor to inject global variables into templates
@app.context_processor
def inject_globals() -> dict:
    """Inject global variables into templates"""
    return {
        "is_logged_in": is_logged_in(),
        "is_exec": is_exec(),
        "colours": colours,
        "stardust": "stardust" in request.path,
    }


@app.route("/")
@app.route("/current/")
@app.route("/upcoming/")
@app.route("/stardust/")
def index() -> str:
    events = group_events(get_upcoming_events())
    return render_template("upcoming.html", events=events)


@app.route("/previous/")
@app.route("/past/")
@app.route("/stardust/previous/")
def previous() -> str:
    events = group_events(get_previous_events())
    return render_template("previous.html", events=events)


@app.route("/api/")
@app.route("/docs/")
@app.route("/api/docs/")
def redirect_to_docs() -> Response:
    """Redirect to the Swagger documentation"""
    return redirect("/apidocs/")


@app.errorhandler(404)
def not_found(error: str) -> tuple[str, int]:
    """404 error handler"""
    return render_template("404.html", error=error), 404


@app.errorhandler(403)
def forbidden(error: str) -> tuple[str, int]:
    """403 error handler"""
    return render_template("403.html", error=error), 403
