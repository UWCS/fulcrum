import base64
import contextlib

from flask import Blueprint, Response, flash, render_template, request

from auth.oauth import is_exec_wrapper
from events.utils import get_week_by_year_term_week
from exec.publicity import create_svg

# TODO: find a better way to convert SVG to PNG
try:
    from cairosvg import svg2png
except OSError:
    import os

    # replace path with the folder where libcairo-2.dll is located
    path = r"C:\Program Files\UniConvertor-2.0rc5\dlls"
    os.environ["path"] += ";" + path  # noqa: SIM112

    with contextlib.suppress(OSError):
        from cairosvg import svg2png

exec_ui_bp = Blueprint("exec_ui", __name__, url_prefix="/exec")


@exec_ui_bp.route("/")
@is_exec_wrapper
def exec_panel() -> str:
    """Exec link panel"""
    return render_template("exec/exec.html")


@exec_ui_bp.route("/publicity/")
def publicity() -> str:
    """Create publicity SVG"""
    year = request.args.get("year")
    term = request.args.get("term")
    start = request.args.get("start_week")
    end = request.args.get("end_week")

    if year is None or term is None or start is None or end is None:
        return render_template("exec/publicity.html")

    start_week = get_week_by_year_term_week(int(year), int(term), int(start))
    end_week = get_week_by_year_term_week(int(year), int(term), int(end))

    if start_week is None or end_week is None:
        messgae = "Invalid "
        if start_week is None:
            messgae += "start "
        if end_week is None:
            if start_week is None:
                messgae += "and "
            messgae += "end "
        messgae += "week"
        flash(messgae, "danger")
        return render_template("exec/publicity.html", year=year, term=term)

    svg = create_svg(start_week, end_week)

    if not svg.startswith("<svg"):
        flash("Failed to create SVG", "danger")

    svg_64 = base64.b64encode(svg.encode("utf-8"))

    return render_template(
        "exec/publicity.html",
        svg=svg,
        svg_64=svg_64.decode("utf-8"),
        year=year,
        term=term,
        start_week=start,
        end_week=end,
    )


@exec_ui_bp.route("/publicity/png/")
def publicity_png() -> str | Response:
    """Convert publicity SVG to PNG"""

    svg_64 = request.args.get("svg", "")

    if not svg_64:
        return "No SVG provided"

    try:
        svg = base64.b64decode(svg_64)
    except Exception:
        return "Invalid base64 SVG"

    try:
        png = svg2png(bytestring=svg)  # type: ignore
    except NameError:
        return """
                <p>Congratulations, you're running windows!</p>
                <p>This means cairosvg can't find libcairo-2.dll</p>
                <p>To install, follow instructions at <a href="https://stackoverflow.com/a/60220855">this stackoverflow answer</a></p>
                <p>then add path to exec/ui.py</p>
            """  # noqa: E501

    return Response(png, mimetype="image/png")
