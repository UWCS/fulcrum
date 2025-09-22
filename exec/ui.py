from flask import Blueprint, flash, render_template, request

from auth.oauth import is_exec_wrapper
from events.utils import get_week_by_year_term_week, get_years
from exec.publicity import create_svg

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
        return render_template("exec/publicity.html", years=get_years())

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
        return render_template(
            "exec/publicity.html", year=year, term=term, years=get_years()
        )

    try:
        svg = create_svg(start_week, end_week)
    except ValueError as e:
        flash(f"Error creating publicity SVG: {e}", "danger")
        return render_template(
            "exec/publicity.html", year=year, term=term, years=get_years()
        )

    return render_template(
        "exec/publicity.html",
        svg=svg,
        years=get_years(),
        year=year,
        term=term,
        start_week=start,
        end_week=end,
    )
