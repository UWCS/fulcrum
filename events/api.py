from datetime import datetime

import pytz
import requests
from flask import Blueprint, Response, jsonify, request
from schema import Event, Tag, Week, db

from auth.auth import is_exec_wrapper

events_bp = Blueprint("events", __name__, url_prefix="/api/events")


@events_bp.route("/<int:year>/<int:term>/<int:week>/<str:slug>", methods=["GET"])
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


@events_bp.route("/<int:event_id>", methods=["GET"])
def get_event_by_id(event_id: int) -> tuple[Response, int]:
    """Get a specific event by its ID."""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    return jsonify(event.to_dict()), 200


@events_bp.route("/<int:year>/<int:term>/<int:week>", methods=["GET"])
def get_events_year_term_week(year: int, term: int, week: int) -> tuple[Response, int]:
    """Get all events for a specific year, term, and week."""
    events = Event.query.filter(
        Event.date.has(
            (Week.academic_year == year) & (Week.term == term) & (Week.week == week)
        )
    ).all()

    if not events:
        return jsonify({"error": "No events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_bp.route("/<int:year>/<int:term>/", methods=["GET"])
def get_events_year_term(year: int, term: int) -> tuple[Response, int]:
    """Get all events for a specific year and term."""
    events = Event.query.filter(
        Event.date.has((Week.academic_year == year) & (Week.term == term))
    ).all()

    if not events:
        return jsonify({"error": "No events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_bp.route("/<int:year>/", methods=["GET"])
def get_events_year(year: int) -> tuple[Response, int]:
    """Get all events for a specific year."""
    events = Event.query.filter(Event.date.has(Week.academic_year == year)).all()

    if not events:
        return jsonify({"error": "No events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_bp.route("/create", methods=["POST"])
@is_exec_wrapper
def create_event() -> tuple[Response, int]:
    """Create a new event"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # convert start_time and end_time to London timezone
        start_time = pytz.timezone("Europe/London").localize(
            datetime.fromisoformat(data["start_time"])
        )
        end_time = (
            pytz.timezone("Europe/London").localize(
                datetime.fromisoformat(data["end_time"])
            )
            if "end_time" in data
            else None
        )

        # create the event object
        event = Event(
            name=data["name"],
            description=data["description"],
            draft=data.get("draft", False),
            location=data["location"],
            location_url=data.get("location_url"),
            icon=data.get("icon"),
            colour=data.get("colour"),
            start_time=start_time,
            end_time=end_time,
        )

        # attach week to the event
        week = get_week_from_date(start_time)
        if week is None:
            return jsonify({"error": "Unable to determine week for the event"}), 400
        event.date = week  # type: ignore

        # attach tags to the event
        tags = data.get("tags", [])
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

        return jsonify(event.to_dict()), 201

    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


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
            # TODO: handle the case where the year is before the API year
            # use json
            week = None

    return week


@events_bp.route("/create_repeat", methods=["POST"])
@is_exec_wrapper
def create_repeat_event() -> str:
    """Create a bunch of events at once"""
    pass


@events_bp.route("/<int:event_id>", methods=["PATCH"])
@is_exec_wrapper
def edit_event(event_id: int) -> str:
    """Edit an existing event"""
    pass


@events_bp.route("/<int:event_id>", methods=["DELETE"])
@is_exec_wrapper
def delete_event(event_id: int) -> str:
    """Delete an existing event"""
    pass
