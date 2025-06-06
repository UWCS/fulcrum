import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template

from auth.auth import auth_bp, configure_oauth, is_exec, is_logged_in
from events.api import events_api_bp

# if .env file exists, load it
if Path(".env").exists():
    load_dotenv()

# initialise flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# setup oauth and add routes
configure_oauth(app)
app.register_blueprint(auth_bp)

# add api routes
app.register_blueprint(events_api_bp, url_prefix="/api/events")


@app.route("/")
def index() -> str:
    return render_template("index.html", is_logged_in=is_logged_in(), is_exec=is_exec())
