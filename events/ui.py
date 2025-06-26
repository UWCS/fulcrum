from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.wrappers import Response

from auth.auth import is_exec_wrapper
from events.utils import (
    create_event,
    get_datetime_from_string,
    get_event_by_slug,
    get_timedelta_from_string,
    validate_colour,
)

events_ui_bp = Blueprint("events_ui", __name__, url_prefix="/events")


@events_ui_bp.route("/create", methods=["GET", "POST"])
@is_exec_wrapper
def create(error: str | None = None) -> str | Response:  # noqa: PLR0911
    # if getting, return the ui for creating an event
    if request.method == "GET":
        return render_template(
            "events/form.html",
            error=error,
            action="events_ui.create",
            method="POST",
            event=None,
        )

    # if posting, create the event

    print("Creating event with data:", request.form)

    # parse colour
    text_colour = request.form.get("text_colour", None)
    color_colour = request.form.get("color_colour", None)

    text_colour = text_colour.strip().lower() if text_colour else None
    color_colour = color_colour.strip().lower() if color_colour else None

    if (colour := validate_colour(text_colour, color_colour)) is not None:
        flash(colour, "error")
        return redirect(url_for("events_ui.create"))

    colour = color_colour if color_colour else text_colour

    # parse dates and duration
    start_time = get_datetime_from_string(request.form["start_time"])
    if isinstance(start_time, str):
        flash(start_time, "error")
        return redirect(url_for("events_ui.create"))

    duration = (
        get_timedelta_from_string(request.form["duration"])
        if request.form["duration"]
        else None
    )
    if isinstance(duration, str):
        flash(duration, "error")
        return redirect(url_for("events_ui.create"))

    end_time = (
        get_datetime_from_string(request.form["end_time"])
        if request.form["end_time"]
        else None
    )
    if isinstance(end_time, str):
        flash(end_time, "error")
        return redirect(url_for("events_ui.create"))

    # parse tags
    tags = (
        [tag.strip() for tag in request.form["tags"].split(",")]
        if request.form["tags"]
        else []
    )

    # attempt to create the event
    event = create_event(
        request.form["name"],
        request.form["description"],
        "draft" in request.form,
        request.form["location"],
        request.form.get("location_url", None),
        request.form.get("icon", None),
        colour,
        start_time,
        duration,
        end_time,
        tags,
    )

    # if failed, redirect to the create page with an error
    if isinstance(event, str):
        flash(event, "error")
        return redirect(url_for("events_ui.create", error=event))

    # if successful, redirect to the event page
    return redirect(
        url_for(
            "events_ui.view",
            year=event.date.academic_year,
            term=event.date.term,
            week=event.date.week,
            slug=event.slug,
        )
    )


# TODO: other event management UI


@events_ui_bp.route("/<int:year>/<int:term>/<int:week>/<string:slug>")
def view(year: int, term: int, week: int, slug: str) -> str:
    """View an event by its year, term, week, and slug."""

    event = get_event_by_slug(year, term, week, slug)

    if event is None:
        return "Event not found"

    return str(event.to_dict())
