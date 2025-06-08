from datetime import datetime, timedelta
from json import load
from pathlib import Path

import pytz
import requests
from flask import Blueprint, Response, jsonify, request
from schema import Event, Tag, Week, db

from auth.auth import is_exec_wrapper

# bind endpoints to /api/events/...
events_api_bp = Blueprint("events", __name__, url_prefix="/api/events")


@events_api_bp.route("/<int:year>/<int:term>/<int:week>/<str:slug>", methods=["GET"])
def get_event(year: int, term: int, week: int, slug: str) -> tuple[Response, int]:
    """Get a specific event by year, term, week, and slug."""
    event = Event.query.filter(
        Event.date.has(
            (Week.academic_year == year) & (Week.term == term) & (Week.week == week)
        ),
        Event.slug == slug,  # type: ignore
    ).first()

    if not event:
        return jsonify({"error": "Event not found"}), 404

    return jsonify(event.to_dict()), 200


@events_api_bp.route("/<int:event_id>", methods=["GET"])
def get_event_by_id(event_id: int) -> tuple[Response, int]:
    """Get a specific event by its ID."""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    return jsonify(event.to_dict()), 200


@events_api_bp.route("/<int:year>/<int:term>/<int:week>", methods=["GET"])
def get_events_year_term_week(year: int, term: int, week: int) -> tuple[Response, int]:
    """Get all events for a specific year, term, and week."""
    events = (
        Event.query.filter(
            Event.date.has(
                (Week.academic_year == year) & (Week.term == term) & (Week.week == week)
            )
        )
        .order_by(Event.start_time, Event.end_time)  # type: ignore
        .all()
    )

    if not events:
        return jsonify({"error": "No events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/<int:year>/<int:term>/", methods=["GET"])
def get_events_year_term(year: int, term: int) -> tuple[Response, int]:
    """Get all events for a specific year and term."""
    events = (
        Event.query.filter(
            Event.date.has((Week.academic_year == year) & (Week.term == term))
        )
        .order_by(Event.start_time, Event.end_time)  # type: ignore
        .all()
    )

    if not events:
        return jsonify({"error": "No events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/<int:year>/", methods=["GET"])
def get_events_year(year: int) -> tuple[Response, int]:
    """Get all events for a specific year."""
    events = (
        Event.query.filter(Event.date.has(Week.academic_year == year))
        .order_by(Event.start_time, Event.end_time)  # type: ignore
        .all()
    )

    if not events:
        return jsonify({"error": "No events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/create", methods=["POST"])
@is_exec_wrapper
def create_event_api() -> tuple[Response, int]:
    """Create a new event"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = [
        "name",
        "description",
        "location",
        "start_time",
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    start_time = pytz.timezone("Europe/London").localize(
        datetime.fromisoformat(data["start_time"])
    )
    if "duration" in data:
        try:
            days, hours, minutes = map(int, data["duration"].split(":"))
            duration = timedelta(days=days, hours=hours, minutes=minutes)
        except ValueError:
            return (
                jsonify(
                    {"error": "Invalid duration format, expected 'days:hours:minutes'"}
                ),
                400,
            )
    else:
        duration = None

    try:
        event = create_event(
            data["name"],
            data["description"],
            data.get("draft", False),
            data["location"],
            data.get("location_url"),
            data.get("icon"),
            data.get("colour"),
            start_time,
            duration,
            data.get("tags", []),
        )
        if isinstance(event, str):
            return jsonify({"error": event}), 400
        return jsonify(event.to_dict()), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


def create_event(  # noqa: PLR0913
    name: str,
    description: str,
    draft: bool,
    location: str,
    location_url: str | None,
    icon: str | None,
    colour: str | None,
    start_time: datetime,
    duration: timedelta | None,
    tags: list[str],
) -> Event | str:
    """Create an event"""
    # convert start_time and calculate end_time
    start_time = pytz.timezone("Europe/London").localize(start_time)
    end_time = start_time + duration if duration else None

    # create the event object
    event = Event(
        name=name,
        description=description,
        draft=draft,
        location=location,
        location_url=location_url,
        icon=icon,
        colour=colour,
        start_time=start_time,
        end_time=end_time,
    )

    # attach week to the event
    event.date = get_week_from_date(start_time)  # type: ignore

    # attach tags to the event
    # check all tags exist, create if not
    for tag in tags:
        tag_obj = Tag.query.filter_by(name=tag).first()
        if not tag_obj:
            tag_obj = Tag(name=tag)
            db.session.add(tag_obj)
        event.tags.append(tag_obj)

    # add the event to the session and commit
    db.session.add(event)
    db.session.commit()

    return event


def get_week_from_date(date: datetime) -> Week | None:
    """Get the week from a given date"""

    week = Week.query.filter(
        (date >= Week.start_date) & (date <= Week.end_date)  # type: ignore
    ).first()

    if week is None:
        # if unable to find week, create the week
        year, month = date.year, date.month
        if month < 9:  # noqa: PLR2004
            # if september or earlier, use the previous academic year
            year -= 1

        api_year = 2006
        if year >= api_year:
            # fetch the term dates from the Warwick API

            warwick_week = requests.get(
                f"https://tabula.warwick.ac.uk/api/v1/termdates/{year}/weeks?numberingSystem=term"
            ).json()

            for w in warwick_week["weeks"]:
                if (
                    datetime.strptime(w["startDate"], "%Y-%m-%d").date()
                    <= date.date()
                    <= datetime.strptime(w["endDate"], "%Y-%m-%d").date()
                ):
                    name = w["name"]
                    if "Term" in name:
                        parts = name.split(",")
                        term_num = int(parts[0].split(" ")[-1])
                        week_num = int(parts[1].split(" ")[-1])
                    else:
                        term_num = 1
                        week_num = 0

                    week = Week(
                        academic_year=year,
                        term=term_num,
                        week=week_num,
                        start_date=datetime.strptime(w["startDate"], "%Y-%m-%d"),
                    )

                    db.session.add(week)
                    db.session.commit()
                    break

        else:
            with Path("olddates.json").open("r") as f:
                old_dates = load(f)
            for w in old_dates:
                if datetime.strptime(w["date"], "%Y-%m-%d").date() <= date.date():
                    week = Week(
                        academic_year=year,
                        term=w["term"],
                        week=w["week"],
                        start_date=datetime.strptime(w["date"], "%Y-%m-%d"),
                    )
                    db.session.add(week)
                    db.session.commit()
                    break

    return week


@events_api_bp.route("/create_repeat", methods=["POST"])
@is_exec_wrapper
def create_repeat_event_api() -> tuple[Response, int]:  # noqa: PLR0911
    """Create a bunch of events at once"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = [
        "name",
        "description",
        "location",
        "start_times",
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    if "duration" in data:
        try:
            days, hours, minutes = map(int, data["duration"].split(":"))
            duration = timedelta(days=days, hours=hours, minutes=minutes)
        except ValueError:
            return (
                jsonify(
                    {"error": "Invalid duration format, expected 'days:hours:minutes'"}
                ),
                400,
            )

    start_times = []
    for start_time_str in data["start_times"]:
        try:
            start_time = pytz.timezone("Europe/London").localize(
                datetime.fromisoformat(start_time_str)
            )
        except ValueError:
            return (
                jsonify({"error": f"Invalid start time format: {start_time_str}"}),
                400,
            )
        start_times.append(start_time)

    try:
        events = create_repeat_event(
            data["name"],
            data["description"],
            data.get("draft", False),
            data["location"],
            data.get("location_url"),
            data.get("icon"),
            data.get("colour"),
            start_times,
            duration,  # type: ignore
            data.get("tags", []),
        )
        if isinstance(events, str):
            return jsonify({"error": events}), 400
        return jsonify([event.to_dict() for event in events]), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


def create_repeat_event(  # noqa: PLR0913
    name: str,
    description: str,
    draft: bool,
    location: str,
    location_url: str | None,
    icon: str | None,
    colour: str | None,
    start_times: list[datetime],
    duration: timedelta | None,
    tags: list[str],
) -> list[Event] | str:
    """Create multiple events at once"""
    events = []  # the created events
    for start_time in start_times:
        # iterate through start_times and create events
        event = create_event(
            name,
            description,
            draft,
            location,
            location_url,
            icon,
            colour,
            start_time,
            duration,
            tags,
        )

        if isinstance(event, str):
            # rollback any created events if an error occurs
            for event in events:
                db.session.delete(event)
            db.session.commit()
            clean_weeks()
            clean_tags()
            return event

        events.append(event)
    return events


@events_api_bp.route("/week/<str:date_str>", methods=["GET"])
def get_week_by_date(date_str: str) -> tuple[Response, int]:
    """Get the week for a specific date"""
    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    week = Week.query.filter(
        (date >= Week.start_date) & (date <= Week.end_date)  # type: ignore
    ).first()

    if not week:
        return jsonify({"error": "Week not found"}), 404

    return jsonify(week.to_dict()), 200


@events_api_bp.route("/<int:event_id>", methods=["PATCH"])
@is_exec_wrapper
def edit_event(event_id: int) -> tuple[Response, int]:
    """Edit an existing event"""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    try:
        event.name = data.get("name", event.name)
        event.slug = event.name.lower().replace(" ", "-")
        event.description = data.get("description", event.description)
        event.draft = data.get("draft", event.draft)
        event.location = data.get("location", event.location)
        event.location_url = data.get("location_url", event.location_url)
        event.icon = data.get("icon", event.icon)
        event.colour = data.get("colour", event.colour)
        event.start_time = pytz.timezone("Europe/London").localize(
            datetime.fromisoformat(data.get("start_time", event.start_time.isoformat()))
        )
        if "duration" in data:
            try:
                days, hours, minutes = map(int, data["duration"].split(":"))
                event.duration = timedelta(days=days, hours=hours, minutes=minutes)
            except ValueError:
                return (
                    jsonify(
                        {
                            "error": "Invalid duration format, expected 'days:hours:minutes'"
                        }
                    ),
                    400,
                )

        # update week if start_time has changed
        if "start_time" in data:
            week = get_week_from_date(event.start_time)
            if week is None:
                return jsonify({"error": "Unable to determine week for the event"}), 400
            event.date = week  # type: ignore

        # update tags
        tags = data.get("tags", [])
        event.tags.clear()  # clear existing tags
        for tag in tags:
            tag_obj = Tag.query.filter_by(name=tag).first()
            if not tag_obj:
                tag_obj = Tag(name=tag)
                db.session.add(tag_obj)
            event.tags.append(tag_obj)

        # commit changes
        db.session.commit()

        # clean up weeks and tags
        clean_weeks()
        clean_tags()

        return jsonify(event.to_dict()), 200
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@events_api_bp.route("/<int:event_id>", methods=["DELETE"])
@is_exec_wrapper
def delete_event(event_id: int) -> tuple[Response, int]:
    """Delete an existing event"""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # commit the deletion
    db.session.delete(event)
    db.session.commit()

    # clean up weeks and tags
    clean_weeks()
    clean_tags()

    return jsonify({"message": "Event deleted successfully"}), 200


def clean_weeks() -> None:
    """Clean weeks that are not associated with any events"""
    weeks = Week.query.all()
    for week in weeks:
        if not week.events:  # type: ignore
            db.session.delete(week)
    db.session.commit()


def clean_tags() -> None:
    """Clean tags that are not associated with any events"""
    tags = Tag.query.all()
    for tag in tags:
        if not tag.events:  # type: ignore
            db.session.delete(tag)
    db.session.commit()


@events_api_bp.route("/tags", methods=["GET"])
def get_tags() -> tuple[Response, int]:
    """Get all tags"""
    tags = Tag.query.order_by(Tag.name).all()
    if not tags:
        return jsonify({"error": "No tags found"}), 404
    return jsonify([tag.to_dict() for tag in tags]), 200


@events_api_bp.route("/tags/<str:tag_name>", methods=["GET"])
def get_tag(tag_name: str) -> tuple[Response, int]:
    """Get all events for a specific tag"""
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        return jsonify({"error": "Tag not found"}), 404

    # get events associated with the tag
    events = tag.events.order_by(Event.start_time, Event.end_time).all()
    if not events:
        return jsonify({"error": "No events found for this tag"}), 404
    return jsonify([event.to_dict() for event in events]), 200
