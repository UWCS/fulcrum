from collections import defaultdict
from datetime import datetime
from typing import Match
from xml.etree import ElementTree as ET

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from markdown import Markdown, markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor
from markupsafe import escape
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.wrappers import Response

from auth.oauth import is_exec, is_exec_wrapper
from config import colours, custom_icons
from events.utils import (
    create_event,
    create_repeat_event,
    delete_event,
    edit_event,
    get_all_tags,
    get_datetime_from_string,
    get_event_by_slug,
    get_events_by_tag,
    get_events_by_time,
    get_timedelta_from_string,
    validate_colour,
)
from schema import Event

events_ui_bp = Blueprint("events_ui", __name__)


def get_event_from_form(form_data: ImmutableMultiDict) -> dict:
    """Get event dict from form data"""
    return {
        "name": form_data["name"],
        "description": form_data["description"],
        "draft": "draft" in form_data,
        "location": form_data["location"],
        "location_url": (
            form_data["location_url"] if form_data["location_url"] != "" else None
        ),
        "icon": form_data["icon"] if form_data["icon"] != "" else None,
        "text_colour": (
            form_data["text_colour"] if form_data["text_colour"] != "" else None
        ),
        "color_colour": (
            form_data["color_colour"] if form_data["color_colour"] != "" else None
        ),
        "times": zip(
            form_data.getlist("start_time[]"), form_data.getlist("end_time[]")
        ),
        "duration": (form_data["duration"] if form_data["duration"] != "" else None),
        "tags": [tag for tag in form_data.getlist("tags[]") if tag],
    }


def parse_form_data(form_data: ImmutableMultiDict) -> dict | str:
    """Parse event from form data"""
    # parse colour
    text_colour = (
        form_data["text_colour"].strip().lower()
        if form_data["text_colour"] != ""
        else None
    )
    color_colour = (
        form_data["color_colour"].strip().lower()
        if form_data["color_colour"] != ""
        else None
    )

    if (error := validate_colour(text_colour, color_colour)) is not None:
        return error

    # prefer text_colour if both are provided (in case these colours change)
    colour = text_colour if text_colour else color_colour

    # parse dates and duration
    start_times = [
        get_datetime_from_string(t) for t in form_data.getlist("start_time[]")
    ]
    for start_time in start_times:
        if isinstance(start_time, str):
            return start_time

    duration = (
        get_timedelta_from_string(form_data["duration"])
        if form_data["duration"] != ""
        else None
    )
    if isinstance(duration, str):
        return duration

    end_times = None
    if form_data.get("end_time") is not None:
        end_times = [
            get_datetime_from_string(t) for t in form_data.getlist("end_time[]")
        ]
        for end_time in end_times:
            if isinstance(end_time, str):
                return end_time

    # parse tags
    tags = form_data.getlist("tags[]")
    tags = [tag.strip().lower() for tag in tags if tag.strip()]

    data = {
        "name": form_data["name"],
        "description": form_data["description"],
        "draft": "draft" in form_data,
        "location": form_data["location"],
        "location_url": (
            form_data["location_url"] if form_data["location_url"] != "" else None
        ),
        "icon": form_data["icon"] if form_data["icon"] != "" else None,
        "colour": colour,
        "duration": duration,
        "tags": tags,
    }

    if len(start_times) == 1:
        data["start_time"] = start_times[0]
        data["end_time"] = end_times[0] if end_times is not None else None
    else:
        data["start_times"] = start_times
        data["end_times"] = end_times if end_times is not None else None

    return data


@events_ui_bp.route("/create/", methods=["GET", "POST"])
@is_exec_wrapper
def create() -> str | Response:
    """Create a new event."""

    tags = [tag.name for tag in get_all_tags()]

    # if getting, return the ui for creating an event
    if request.method == "GET":
        return render_template(
            "events/form.html",
            action="events_ui.create",
            method="POST",
            icons=custom_icons,
            colours=colours,
            tags=tags,
        )

    # if posting, create the event

    # parse form data
    user_event = get_event_from_form(request.form)
    data = parse_form_data(request.form)
    if isinstance(data, str):
        return render_template(
            "events/form.html",
            action="events_ui.create",
            method="POST",
            error=data,
            event=user_event,
            icons=custom_icons,
            colours=colours,
            tags=tags,
        )

    # attempt to create the event
    if "start_time" in data:
        event = create_event(**data)
    else:
        event = create_repeat_event(**data)

    # if failed, return the form with an error
    if isinstance(event, str):
        return render_template(
            "events/form.html",
            action="events_ui.create",
            method="POST",
            error=event,
            event=user_event,
            icons=custom_icons,
            colours=colours,
            tags=tags,
        )

    if isinstance(event, list):
        event = event[0]

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


@events_ui_bp.route(
    "/<int:year>/<int:term>/<int:week>/<string:slug>/edit/", methods=["GET", "POST"]
)
@is_exec_wrapper
def edit(year: int, term: int, week: int, slug: str) -> str | Response:
    """Edit an existing event by its year, term, week, and slug."""

    event = get_event_by_slug(year, term, week, slug)

    if event is None:
        return abort(404, description="Event not found")

    tags = [tag.name for tag in get_all_tags()]

    # if getting, return the ui for editing the event
    if request.method == "GET":
        return render_template(
            "events/form.html",
            action="events_ui.edit",
            method="POST",
            event=event,
            icons=custom_icons,
            colours=colours,
            tags=tags,
        )

    # if posting, update the event

    # parse form data
    user_event = get_event_from_form(request.form)
    user_event["date"] = event.date.to_dict()
    data = parse_form_data(request.form)
    if isinstance(data, str):
        return render_template(
            "events/form.html",
            action="events_ui.edit",
            method="POST",
            error=data,
            event=user_event,
            icons=custom_icons,
            colours=colours,
            tags=tags,
        )

    # attempt to edit the event
    event = edit_event(event.id, **data)

    # if failed, redirect to the edit page with an error
    if isinstance(event, str):
        return render_template(
            "events/form.html",
            action="events_ui.edit",
            method="POST",
            error=event,
            event=user_event,
            icons=custom_icons,
            colours=colours,
            tags=tags,
        )

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


@events_ui_bp.route(
    "/<int:year>/<int:term>/<int:week>/<string:slug>/delete/", methods=["POST"]
)
@is_exec_wrapper
def delete(year: int, term: int, week: int, slug: str) -> Response:
    """Delete an event by its year, term, week, and, slug"""

    event = get_event_by_slug(year, term, week, slug)

    if event is None:
        return abort(404, description="Event not found")

    delete_event(event.id)

    flash("Event deleted successfully", "success")

    return redirect("/")


# shamelessly stolen from docs (https://python-markdown.github.io/extensions/api/#example_3)
# allows for markdown strikethrough
class DelInlineProcessor(InlineProcessor):
    def handleMatch(  # noqa: N802
        self, m: Match[str], data: str  # noqa: ARG002
    ) -> tuple[ET.Element, int, int]:
        el = ET.Element("del")
        el.text = m.group(1)
        return el, m.start(0), m.end(0)


class DelExtension(Extension):
    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802
        del_pattern = r"~~(.*?)~~"  # like ~~del~~
        md.inlinePatterns.register(DelInlineProcessor(del_pattern, md), "del", 175)


# convert links to target="_blank"
class TargetTreeprocessor(Treeprocessor):
    def run(self, root: ET.Element) -> None:
        for element in root.iter("a"):
            element.set("target", "_blank")


class TargetExtension(Extension):
    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802
        md.treeprocessors.register(TargetTreeprocessor(md), "target", 15)


def prepare_event(event: Event) -> dict:
    """Prepare an event for rendering"""

    event_dict = event.to_dict()

    # convert start and end times back to datetime
    event_dict["start_time"] = datetime.fromisoformat(event_dict["start_time"])
    if event_dict["end_time"]:
        event_dict["end_time"] = datetime.fromisoformat(event_dict["end_time"])

    # convert colour to hex
    if event_dict["colour"] in colours:
        event_dict["colour"] = colours[event_dict["colour"]]
    if not event_dict["colour"].startswith("#"):
        event_dict["colour"] = f"#{event_dict["colour"]}"

    # convert markdown to html
    event_dict["description"] = markdown(
        escape(event_dict["description"]),
        extensions=[DelExtension(), TargetExtension()],
    )

    return event_dict


@events_ui_bp.route("/<int:year>/<int:term>/<int:week>/<string:slug>/")
def view(year: int, term: int, week: int, slug: str) -> str:
    """View an event by its year, term, week, and slug."""

    event = get_event_by_slug(year, term, week, slug)

    if event is None:
        return abort(404, description="Event not found")

    event = prepare_event(event)

    return render_template(
        "events/event.html",
        event=event,
    )


def group_events(events: list[Event]) -> list[dict]:
    """Group events by term, week, and day"""

    # initalise dictionary
    # this is not too nested i have no clue what youre talking about
    grouped_events = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    )

    # for each event, group by term, week, and day
    for event in events:
        year = event.date.academic_year
        term = event.date.term
        week = event.date.week
        day = event.start_time.strftime("%A")
        grouped_events[year][term][week][day].append(event)

    # combine into a list of dictionaries
    year_list = []
    for year, terms in grouped_events.items():
        term_list = []
        for term, weeks in terms.items():
            week_list = []
            for week, days in weeks.items():
                day_list = []
                # get start_date of the week from the first event
                start_date = next(iter(days.values()))[0].date.start_date
                for day, day_events in days.items():
                    day_list.append(
                        {
                            "day": day,
                            "events": [prepare_event(event) for event in day_events],
                        }
                    )
                week_list.append(
                    {"week": week, "days": day_list, "start_date": start_date}
                )
            term_list.append({"term": term, "weeks": week_list})
        year_list.append({"year": year, "terms": term_list})
    return year_list


@events_ui_bp.route("/<int:year>/")
@events_ui_bp.route("/<int:year>/<int:term>/")
@events_ui_bp.route("/<int:year>/<int:term>/<int:week>/")
def view_list(year: int, term: int | None = None, week: int | None = None) -> str:
    """View all events in a time frame in list form"""

    events = get_events_by_time(year, term, week, draft=is_exec())

    if not events:
        return abort(404, description="No events found for this week")

    events = group_events(events)

    return render_template(
        "events/list.html", events=events, year=year, term=term, week=week
    )


@events_ui_bp.route("/tags/<string:tag>/")
def view_tag(tag: str) -> str:
    """View all events associated with a tag"""

    events = get_events_by_tag(tag)

    if not events:
        return abort(404, description="No events found for this tag")

    events = [prepare_event(event) for event in events]

    return ", ".join(event["name"] for event in events)
