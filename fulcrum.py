import os
from json import load
from pathlib import Path

from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, redirect, render_template
from werkzeug.wrappers import Response

from auth.api import auth_api_bp, auth_ui_bp
from auth.oauth import auth_bp, configure_oauth, is_exec, is_logged_in
from events.api import events_api_bp
from events.ui import events_ui_bp
from schema import initialise_db

# if .env file exists, load it
if Path(".env").exists():
    load_dotenv()

# initialise flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# initialise database
initialise_db(app)

# setup oauth and add routes
configure_oauth(app)
app.register_blueprint(auth_bp)
app.register_blueprint(auth_ui_bp, url_prefix="/auth")

# add api routes
app.register_blueprint(events_api_bp, url_prefix="/api/events")
app.register_blueprint(auth_api_bp, url_prefix="/api/auth")

# setup Swagger
with Path("swagger.json").open("r") as f:
    swagger = Swagger(app, template=load(f))


# add event ui routes
app.register_blueprint(events_ui_bp)


# context processor to inject global variables into templates
@app.context_processor
def inject_globals() -> dict:
    """Inject global variables into templates"""
    return {
        "is_logged_in": is_logged_in(),
        "is_exec": is_exec(),
    }


@app.route("/")
def index() -> str:
    return render_template("index.html")


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
