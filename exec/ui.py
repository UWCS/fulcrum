from flask import Blueprint, render_template

from auth.oauth import is_exec_wrapper
from exec.publicity import create_svg

exec_ui_bp = Blueprint("exec_ui", __name__, url_prefix="/exec")


@exec_ui_bp.route("/")
@is_exec_wrapper
def exec_panel() -> str:
    """Exec link panel"""
    return render_template("exec/exec.html")


@exec_ui_bp.route("/publicity/")
def publicity() -> str:
    return render_template("exec/publicity.html")
