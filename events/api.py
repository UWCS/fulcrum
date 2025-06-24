from datetime import datetime

from flask import Blueprint, Response, jsonify, request

from auth.auth import valid_api_auth
from events.utils import (
    create_event,
    create_repeat_event,
    delete_event,
    edit_event,
    get_datetime_from_string,
    get_event_by_id,
    get_event_by_slug,
    get_events_by_time,
    get_timedelta_from_string,
)
from schema import Event, Tag, Week

# bind endpoints to /api/events/...
events_api_bp = Blueprint("events_api", __name__, url_prefix="/api/events")


@events_api_bp.route("/<int:year>/<int:term>/<int:week>/<string:slug>", methods=["GET"])
def get_event(year: int, term: int, week: int, slug: str) -> tuple[Response, int]:
    """Get a specific event by year, term, week, and slug.
    ---
    parameters:
      - name: year
        in: path
        type: integer
        required: true
        description: The academic year of the event.
      - name: term
        in: path
        type: integer
        required: true
        description: The term of the event.
      - name: week
        in: path
        type: integer
        required: true
        description: The week of the event.
      - name: slug
        in: path
        type: string
        required: true
        description: The slug of the event.
    security: []
    responses:
        200:
            description: A JSON object containing the event details.
            schema:
                $ref: '#/definitions/Event'
        404:
            description: Event not found.
    """
    event = get_event_by_slug(year, term, week, slug)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    return jsonify(event.to_dict()), 200


@events_api_bp.route("/<int:event_id>", methods=["GET"])
def get_event_by_id_api(event_id: int) -> tuple[Response, int]:
    """Get a specific event by its ID.
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: The ID of the event.
    security: []
    responses:
        200:
            description: A JSON object containing the event details.
            schema:
                $ref: '#/definitions/Event'
        404:
            description: Event not found.
    """
    event = get_event_by_id(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    return jsonify(event.to_dict()), 200


@events_api_bp.route("/<int:year>/<int:term>/<int:week>", methods=["GET"])
@events_api_bp.route("/<int:year>/<int:term>", methods=["GET"])
@events_api_bp.route("/<int:year>", methods=["GET"])
def get_events(
    year: int, term: int | None = None, week: int | None = None
) -> tuple[Response, int]:
    """Get all events for a specific year, term, and week.
    ---
    parameters:
      - name: year
        in: path
        type: integer
        required: true
        description: The academic year of the events.
      - name: term
        in: path
        type: integer
        required: false
        description: The term of the events.
      - name: week
        in: path
        type: integer
        required: false
        description: The week of the events.
      - name: drafts
        in: query
        type: boolean
        required: false
        default: false
        description: Whether to include draft events.
    security: []
    responses:
        200:
            description: A JSON array containing the events.
            schema:
                type: array
                items:
                    $ref: '#/definitions/Event'
        404:
            description: No events found.
    """

    include_drafts = request.args.get("drafts", "false").lower() == "true"

    events = get_events_by_time(year, term, week, include_drafts)

    if not events:
        return jsonify({"error": "No events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/create", methods=["POST"])
@valid_api_auth
def create_event_api() -> tuple[Response, int]:  # noqa: PLR0911
    """Create a new event
    ---
    parameters:
      - name: name
        in: body
        type: string
        required: true
        description: The name of the event.
      - name: description
        in: body
        type: string
        required: true
        description: The description of the event.
      - name: location
        in: body
        type: string
        required: true
        description: The location of the event.
      - name: start_time
        in: body
        type: string
        required: true
        description: The start time of the event in 'YYYY-MM-DD' format.
      - name: end_time
        in: body
        type: string
        required: false
        description: The end time of the event in 'YYYY-MM-DD' format (if duration also provided must match the duration).
      - name: duration
        in: body
        type: string
        required: false
        description: The duration of the event in 'days:hours:minutes' format (if end_time also provided must match the end_time).
      - name: draft
        in: body
        type: boolean
        required: false
        default: false
        description: Whether the event is a draft.
      - name: location_url
        in: body
        type: string
        required: false
        description: The URL for the location of the event.
      - name: icon
        in: body
        type: string
        required: false
        description: The icon for the event.
      - name: colour
        in: body
        type: string
        required: false
        description: The colour for the event (can either be a hex code or a role colour).
      - name: tags
        in: body
        type: array
        items:
            type : string
            example : "tag1"
            example : "tag2"
        required: false
        default: []
        description: A list of tags associated with the event.
    responses:
        201:
            description: The created event.
            schema:
                $ref: '#/definitions/Event'
        400:
            description: Bad request, missing or invalid data.
        403:
            description: Forbidden.
    """  # noqa: E501
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

    start_time = get_datetime_from_string(data["start_time"])
    if isinstance(start_time, str):
        return jsonify({"error": start_time}), 400

    end_time = (
        get_datetime_from_string(data.get("end_time")) if data.get("end_time") else None
    )
    if isinstance(end_time, str):
        return jsonify({"error": end_time}), 400

    if "duration" in data:
        duration = get_timedelta_from_string(data["duration"])
        if isinstance(duration, str):
            return jsonify({"error": duration}), 400
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
            end_time,
            data.get("tags", []),
        )
        if isinstance(event, str):
            return jsonify({"error": event}), 400
        return jsonify(event.to_dict()), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@events_api_bp.route("/create_repeat", methods=["POST"])
@valid_api_auth
def create_repeat_event_api() -> tuple[Response, int]:  # noqa: PLR0911
    """Create a bunch of events at once
    ---
    parameters:
      - name: name
        in: body
        type: string
        required: true
        description: The name of the event.
      - name: description
        in: body
        type: string
        required: true
        description: The description of the event.
      - name: location
        in: body
        type: string
        required: true
        description: The location of the event.
      - name: start_times
        in: body
        type: array
        items:
          type : string
          example : "2023-10-01"
          example : "2023-10-08"
        required: true
        description: A list of start times for the events in 'YYYY-MM-DD' format.
      - name: end_times
        in: body
        type: array
        items:
          type : string
          example : "2023-10-01"
          example : "2023-10-08"
        required: false
        description: A list of end times for the events in 'YYYY-MM-DD' format (if duration also provided must match the duration).
      - name: duration
        in: body
        type: string
        required: false
        description: The duration of the events in 'days:hours:minutes' format (if end_times also provided must match the end_times).
      - name: draft
        in: body
        type: boolean
        required: false
        default: false
        description: Whether the events are drafts.
      - name: location_url
        in: body
        type: string
        required: false
        description: The URL for the location of the events.
      - name: icon
        in: body
        type: string
        required: false
        description: The icon for the events.
      - name: colour
        in: body
        type: string
        required: false
        description: The colour for the events (can either be a hex code or a role colour).
      - name: tags
        in: body
        type: array
        items:
          type : string
          example : "tag1"
          example : "tag2"
        required: false
        default: []
        description: A list of tags associated with the events.
    responses:
        201:
            description: The created events.
            schema:
                type: array
                items:
                    $ref: '#/definitions/Event'
        400:
            description: Bad request, missing or invalid data.
        403:
            description: Forbidden.
    """  # noqa: E501
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
        duration = get_timedelta_from_string(data["duration"])
        if isinstance(duration, str):
            return jsonify({"error": duration}), 400
    else:
        duration = None

    start_times = []
    for start_time_str in data["start_times"]:
        start_time = get_datetime_from_string(start_time_str)
        if isinstance(start_time, str):
            return jsonify({"error": start_time}), 400
        start_times.append(start_time)

    end_times = []
    for end_time_str in data.get("end_times", []):
        end_time = get_datetime_from_string(end_time_str)
        if isinstance(end_time, str):
            return jsonify({"error": end_time}), 400
        end_times.append(end_time)

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
            end_times,
            data.get("tags", []),
        )
        if isinstance(events, str):
            return jsonify({"error": events}), 400
        return jsonify([event.to_dict() for event in events]), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@events_api_bp.route("/<int:event_id>", methods=["PATCH"])
@valid_api_auth
def edit_event_api(event_id: int) -> tuple[Response, int]:
    """Edit an existing event
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: The ID of the event to edit.
      - name: name
        in: body
        type: string
        required: false
        description: The new name of the event.
      - name: description
        in: body
        type: string
        required: false
        description: The new description of the event.
      - name: location
        in: body
        type: string
        required: false
        description: The new location of the event.
      - name: start_time
        in: body
        type: string
        required: false
        description: The new start time of the event in 'YYYY-MM-DD' format.
      - name: end_time
        in: body
        type: string
        required: false
        description: The new end time of the event in 'YYYY-MM-DD' format (if duration also provided must match the duration).
      - name: duration
        in: body
        type: string
        required: false
        description: The new duration of the event in 'days:hours:minutes' format (if end_time also provided must match the end_time).
      - name: draft
        in: body
        type: boolean
        required: false
        default: false
        description: Whether the event is a draft.
      - name: location_url
        in: body
        type: string
        required: false
        description: The new URL for the location of the event.
      - name: icon
        in: body
        type: string
        required: false
        description: The new icon for the event.
      - name: colour
        in: body
        type: string
        required: false
        description: The new colour for the event (can either be a hex code or a role colour).
      - name: tags
        in: body
        type: array
        items:
            type : string
            example : "tag1"
            example : "tag2"
        required: false
        default: []
        description: A list of new tags associated with the event.
    responses:
        200:
            description: The updated event.
            schema:
                $ref: '#/definitions/Event'
        400:
            description: Bad request, missing or invalid data.
        403:
            description: Forbidden.
        404:
            description: Event not found.
    """  # noqa: E501

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # convert strings to time objects
    if "start_time" in data:
        start_time = get_datetime_from_string(data["start_time"])
        if isinstance(start_time, str):
            return jsonify({"error": start_time}), 400

    if "end_time" in data:
        end_time = get_datetime_from_string(data["end_time"])
        if isinstance(end_time, str):
            return jsonify({"error": end_time}), 400

    if "duration" in data:
        duration = get_timedelta_from_string(data["duration"])
        if isinstance(duration, str):
            return jsonify({"error": duration}), 400

    event = edit_event(
        event_id,
        data.get("name"),
        data.get("description"),
        data.get("draft", False),
        data.get("location"),
        data.get("location_url"),
        data.get("icon"),
        data.get("colour"),
        start_time if "start_time" in data else None,  # type: ignore
        duration if "duration" in data else None,  # type: ignore
        end_time if "end_time" in data else None,  # type: ignore
        data.get("tags", []),
    )

    if isinstance(event, str):
        return jsonify({"error": event}), 400

    return jsonify(event.to_dict()), 200


@events_api_bp.route("/<int:event_id>", methods=["DELETE"])
@valid_api_auth
def delete_event_api(event_id: int) -> tuple[Response, int]:
    """
    Delete an existing event
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: The ID of the event to delete.
    responses:
        200:
            description: Event deleted successfully.
        400:
            description: Bad request, unable to delete event.
        403:
            description: Forbidden.
        404:
            description: Event not found.
    """

    status = delete_event(event_id)

    if isinstance(status, str):
        return jsonify({"error": status}), 404

    if not status:
        return jsonify({"error": "Unable to delete event"}), 400

    return jsonify({"message": "Event deleted successfully"}), 200


# TODO: might want to refactor getting tags to utils


@events_api_bp.route("/tags", methods=["GET"])
def get_tags() -> tuple[Response, int]:
    """Get all tags
    ---
    security: []
    responses:
        200:
            description: A JSON array containing all tags.
            schema:
                type: array
                items:
                    $ref: '#/definitions/Tag'
        404:
            description: No tags found.
    """
    tags = Tag.query.order_by(Tag.name).all()
    if not tags:
        return jsonify({"error": "No tags found"}), 404
    return jsonify([tag.to_dict() for tag in tags]), 200


@events_api_bp.route("/tags/<string:tag_name>", methods=["GET"])
def get_tag(tag_name: str) -> tuple[Response, int]:
    """Get all events for a specific tag
    ---
    parameters:
      - name: tag_name
        in: path
        type: string
        required: true
        description: The name of the tag.
    security: []
    responses:
        200:
            description: A JSON array containing the events associated with the tag.
            schema:
                type: array
                items:
                    $ref: '#/definitions/Event'
        404:
            description: Tag not found or no events found for this tag.
    """
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        return jsonify({"error": "Tag not found"}), 404

    # get events associated with the tag
    events = tag.events.order_by(Event.start_time, Event.end_time, Event.name).all()
    if not events:
        return jsonify({"error": "No events found for this tag"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/week/<string:date_str>", methods=["GET"])
def get_week_by_date(date_str: str) -> tuple[Response, int]:
    """Get the week for a specific date
    ---
    parameters:
      - name: date_str
        in: path
        type: string
        required: true
        description: The date in 'YYYY-MM-DD' format.
    security: []
    responses:
        200:
            description: A JSON object containing the week details.
            schema:
                $ref: '#/definitions/Week'
        400:
            description: Invalid date format.
        404:
            description: Week not found for the given date.
    """
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
