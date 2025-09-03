from flask import Blueprint, Response, jsonify, request

from auth.api import valid_api_auth
from config import colours, icons
from events.utils import (
    create_event,
    create_repeat_event,
    delete_event,
    edit_event,
    get_all_tags,
    get_datetime_from_string,
    get_days_events,
    get_event_by_id,
    get_event_by_slug,
    get_events_by_time,
    get_previous_events,
    get_tags_by_string,
    get_upcoming_events,
    get_week_by_date,
)
from schema import Event, Tag

# bind endpoints to /api/events/...
events_api_bp = Blueprint("events_api", __name__, url_prefix="/api/events")


@events_api_bp.route(
    "/<int:year>/<int:term>/<sint:week>/<string:slug>/", methods=["GET"]
)
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


@events_api_bp.route("/id/<int:event_id>/", methods=["GET"])
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


@events_api_bp.route("/<int:year>/<int:term>/<sint:week>/", methods=["GET"])
@events_api_bp.route("/<int:year>/<int:term>/", methods=["GET"])
@events_api_bp.route("/<int:year>/", methods=["GET"])
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


@events_api_bp.route("/upcoming/", methods=["GET"])
def get_upcoming_events_api() -> tuple[Response, int]:
    """Get all upcoming events
    ---
    security: []
    parameters:
      - name: drafts
        in: query
        type: boolean
        required: false
        default: false
        description: Whether to include draft events.
    responses:
        200:
            description: A JSON array containing all upcoming events.
            schema:
                type: array
                items:
                    $ref: '#/definitions/Event'
        404:
            description: No upcoming events found.
    """
    include_drafts = request.args.get("drafts", "false").lower() == "true"

    events = get_upcoming_events(include_drafts)

    if not events:
        return jsonify({"error": "No upcoming events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/previous/", methods=["GET"])
def get_previous_events_api() -> tuple[Response, int]:
    """Get all previous events
    ---
    security: []
    parameters:
      - name: drafts
        in: query
        type: boolean
        required: false
        default: false
        description: Whether to include draft events.
    responses:
        200:
            description: A JSON array containing all previous events.
            schema:
                type: array
                items:
                    $ref: '#/definitions/Event'
        404:
            description: No previous events found.
    """
    include_drafts = request.args.get("drafts", "false").lower() == "true"

    events = get_previous_events(include_drafts)

    if not events:
        return jsonify({"error": "No previous events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/days/", methods=["GET"])
def get_days() -> tuple[Response, int]:
    """Get all events from the next <days> days
    ---
    parameters:
      - name: days
        in: query
        type: integer
        required: false
        default: 7
        description: The number of days to look ahead for events.
    responses:
        200:
            description: A JSON array containing the events.
            schema:
                type: array
                items:
                    $ref: '#/definitions/Event'
        400:
            description: Bad request, invalid number of days.
        404:
            description: No events found.
    """

    days = request.args.get("days", "7")
    try:
        days = int(days)
        if days < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid number of days"}), 400

    events = get_days_events(days)

    if not events:
        return jsonify({"error": "No events found"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/create/", methods=["POST"])
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
        description: The start time of the event in 'YYYY-MM-DDTHH:MM' format.
      - name: end_time
        in: body
        type: string
        required: true
        description: The end time of the event in 'YYYY-MM-DDTHH:MM' format.
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
        "end_time",
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    start_time = get_datetime_from_string(data["start_time"])
    if isinstance(start_time, str):
        return jsonify({"error": start_time}), 400

    end_time = get_datetime_from_string(data.get("end_time"))
    if isinstance(end_time, str):
        return jsonify({"error": end_time}), 400

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
            end_time,
            data.get("tags", []),
        )
        if isinstance(event, str):
            return jsonify({"error": event}), 400
        return jsonify(event.to_dict()), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@events_api_bp.route("/create_repeat/", methods=["POST"])
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
          example : "2025-06-24T22:05"
          example : "2025-06-25T12:05"
        required: true
        description: A list of start times for the events in 'YYYY-MM-DD' format.
      - name: end_times
        in: body
        type: array
        items:
          type : string
          example : "2025-06-24T23:05"
          example : "2025-06-25T13:05"
        required: true
        description: A list of end times for the events in 'YYYY-MM-DD' format.
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
        "end_times",
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    start_times = []
    for start_time_str in data["start_times"]:
        start_time = get_datetime_from_string(start_time_str)
        if isinstance(start_time, str):
            return jsonify({"error": start_time}), 400
        start_times.append(start_time)

    end_times = []
    for end_time_str in data["end_times"]:
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
            end_times,
            data.get("tags", []),
        )
        if isinstance(events, str):
            return jsonify({"error": events}), 400
        return jsonify([event.to_dict() for event in events]), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@events_api_bp.route("/<int:event_id>/", methods=["PATCH"])
@valid_api_auth
def edit_event_api(event_id: int) -> tuple[Response, int]:  # noqa: PLR0911, PLR0912
    """Edit an existing event. Leave a field out to leave it unchanged, or as an empty string to clear it.
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
        description: The new start time of the event in 'YYYY-MM-DDTHH:MM' format.
      - name: end_time
        in: body
        type: string
        required: true
        description: The new end time of the event in 'YYYY-MM-DDTHH:MM' format.
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

    event = {}

    if "name" in data:
        if data["name"] == "":
            return jsonify({"error": "Name cannot be empty"}), 400
        event["name"] = data["name"]

    if "description" in data:
        if data["description"] == "":
            return jsonify({"error": "Description cannot be empty"}), 400
        event["description"] = data["description"]

    if "draft" in data:
        if not isinstance(data["draft"], bool):
            return jsonify({"error": "Draft must be a boolean"}), 400
        event["draft"] = data["draft"]

    if "location" in data:
        if data["location"] == "":
            return jsonify({"error": "Location cannot be empty"}), 400
        event["location"] = data["location"]

    if "location_url" in data:
        event["location_url"] = data["location_url"]

    if "icon" in data:
        event["icon"] = data["icon"]

    if "colour" in data:
        event["colour"] = data["colour"]

    # convert strings to time objects
    if "start_time" in data:
        if data["start_time"] == "":
            return jsonify({"error": "Start time cannot be empty"}), 400
        event["start_time"] = get_datetime_from_string(data["start_time"])
        if isinstance(event["start_time"], str):
            return jsonify({"error": event["start_time"]}), 400

    if "end_time" in data:
        if data["end_time"] == "":
            return jsonify({"error": "End time cannot be empty"}), 400
        event["end_time"] = get_datetime_from_string(data["end_time"])
        if isinstance(event["end_time"], str):
            return jsonify({"error": event["end_time"]}), 400

    if "tags" in data:
        if not isinstance(data["tags"], list):
            return jsonify({"error": "Tags must be a list"}), 400
        if any(not isinstance(tag, str) for tag in data["tags"]):
            return jsonify({"error": "All tags must be strings"}), 400
        event["tags"] = data["tags"]

    event = edit_event(event_id, **event)

    if isinstance(event, str):
        return jsonify({"error": event}), 400

    return jsonify(event.to_dict()), 200


@events_api_bp.route("/<int:event_id>/", methods=["DELETE"])
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


@events_api_bp.route("/tags/", methods=["GET"])
def get_tags() -> tuple[Response, int]:
    """Get all tags
    ---
    parameters:
      - name: query
        in: query
        type: string
        required: false
        description: A query string to filter tags by name.
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
    query_string = request.args.get("query", "").lower()
    tags = (
        get_tags_by_string(query_string, limit=-1) if query_string else get_all_tags()
    )
    if not tags:
        return jsonify({"error": "No tags found"}), 404
    return jsonify([tag.to_dict() for tag in tags]), 200


@events_api_bp.route("/tags/<string:tag_name>/", methods=["GET"])
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
    tag = Tag.query.filter_by(name=tag_name.lower()).first()
    if not tag:
        return jsonify({"error": "Tag not found"}), 404

    # get events associated with the tag
    events = tag.events.order_by(Event.start_time, Event.end_time, Event.name).all()
    if not events:
        return jsonify({"error": "No events found for this tag"}), 404
    return jsonify([event.to_dict() for event in events]), 200


@events_api_bp.route("/week/<string:date_str>/", methods=["GET"])
def get_week_by_date_api(date_str: str) -> tuple[Response, int]:
    """Get the week for a specific date
    ---
    parameters:
      - name: date_str
        in: path
        type: string
        required: true
        description: The date in 'YYYY-MM-DDTHH:MM' format.
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
    date = get_datetime_from_string(date_str)
    if isinstance(date, str):
        return jsonify({"error": date}), 400

    week = get_week_by_date(date)

    if not week:
        return jsonify({"error": "Week not found"}), 404

    return jsonify(week.to_dict()), 200


@events_api_bp.route("/colours/", methods=["GET"])
def get_colours() -> tuple[Response, int]:
    """Get all available colours
    ---
    security: []
    responses:
        200:
            description: A JSON object containing all available colours.
            schema:
                type: object
                additionalProperties:
                    type: string
        404:
            description: No colours found.
    """
    if not colours:
        return jsonify({"error": "No colours found"}), 404
    return jsonify(colours), 200


@events_api_bp.route("/icons/", methods=["GET"])
def get_icons() -> tuple[Response, int]:
    """Get all available icons
    ---
    security: []
    responses:
        200:
            description: A JSON object containing all available icons.
            schema:
                type: object
                additionalProperties:
                    type: string
        404:
            description: No icons found.
    """
    if not icons:
        return jsonify({"error": "No icons found"}), 404
    return jsonify(icons), 200
