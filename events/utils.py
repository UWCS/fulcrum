from datetime import datetime, timedelta
from json import load
from pathlib import Path

import pytz
import requests

from config import colours, phosphor_icons, room_mapping
from schema import Event, Tag, Week, db


def get_timedelta_from_string(duration_str: str) -> timedelta | str:
    """Convert a duration string in the format 'days:hours:minutes' to a timedelta."""
    try:
        days, hours, minutes = map(int, duration_str.split(":"))
        return timedelta(days=days, hours=hours, minutes=minutes)
    except ValueError:
        return "Invalid duration format, expected 'days:hours:minutes'"


def get_datetime_from_string(date_str: str) -> datetime | str:
    """Convert a date string in the format 'YYYY-MM-DDTHH:MM' to a datetime object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M").astimezone(
            pytz.timezone("Europe/London")
        )
    except ValueError:
        return "Invalid date format, expected 'YYYY-MM-DDTHH:MM'"


def get_date_from_string(date_str: str) -> datetime | str:
    """Convert a date string in the format 'YYYY-MM-DD' to a datetime object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").astimezone(
            pytz.timezone("Europe/London")
        )
    except ValueError:
        return "Invalid date format, expected 'YYYY-MM-DD'"


def create_event(  # noqa: PLR0912, PLR0913
    name: str,
    description: str,
    draft: bool,
    location: str,
    location_url: str | None,
    icon: str | None,
    colour: str | None,
    start_time: datetime,
    duration: timedelta | None,
    end_time: datetime | None,
    tags: list[str],
) -> Event | str:
    """Create an event"""

    # convert start_time and normalise end_time
    start_time = start_time.astimezone(pytz.timezone("Europe/London"))

    if end_time is None:
        end_time = start_time + duration if duration else None
    else:
        end_time = end_time.astimezone(pytz.timezone("Europe/London"))
        if duration is not None and end_time != start_time + duration:
            return "End time does not match the duration"
    if end_time and end_time < start_time:
        return "End time cannot be before start time"

    # convert icon to lowercase and append ph- if necessary
    icon = icon.lower() if icon else None
    if icon in phosphor_icons:
        icon = f"ph-{icon}"

    if location is not None and location_url is None:
        temp_location = location.lower()
        if temp_location in room_mapping:
            # if location is in the mapping, use the canonical name
            temp_location = room_mapping[temp_location]

        url = f"https://hub.smartne.com/api/store/projects/warwick/live/locations/search/{temp_location}?limit=1"

        response = requests.get(url, timeout=5)
        if response.status_code == 200:  # noqa: PLR2004
            data = response.json()
            if len(data) > 0:
                id = data[0]["_id"]
                location_url = f"https://campus.warwick.ac.uk/search/{id}"

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

    # validate the event
    if error := event.validate():
        db.session.rollback()
        return error

    # create week from the start_time
    week = get_week_from_date(start_time)
    if week is None:
        db.session.rollback()
        return "Unable to find or create a week for the event date"

    # check if week and slug are unique
    if get_event_by_slug(week.academic_year, week.term, week.week, event.slug):
        db.session.rollback()
        return (
            f"An event with the name '{event.slug}' already exists in "
            f"{week.academic_year} t{week.term} w{week.week}"
        )

    # add the event to db to allow tags
    db.session.add(event)

    # attach tags to the event
    # check all tags exist, create if not
    for tag in tags:
        tag = tag.lower()  # noqa: PLW2901
        tag_obj = Tag.query.filter_by(name=tag).first()
        if not tag_obj:
            tag_obj = Tag(name=tag)
            db.session.add(tag_obj)
        event.tags.append(tag_obj)

    db.session.commit()

    return event


def get_week_from_date(date: datetime) -> Week | None:  # noqa: PLR0911, PLR0912
    """Get the week from a given date"""

    week = Week.query.filter(
        (date.date() >= Week.start_date) & (date.date() <= Week.end_date)  # type: ignore
    ).first()

    if week:
        return week

    # if unable to find week, create the week
    year, month = date.year, date.month
    if month < 9:  # noqa: PLR2004
        # if earlier than september, use the previous academic year
        year -= 1

    api_cutoff = 2006
    if year >= api_cutoff:
        # if before cutoff, use the API
        try:
            warwick_week = requests.get(
                f"https://tabula.warwick.ac.uk/api/v1/termdates/{year}/weeks?numberingSystem=term",
                timeout=5,
            )
        except requests.exceptions.SSLError:
            return None

        warwick_week = warwick_week.json()
        week_delta = 0  # the number of weeks in a holiday we are

        for w in warwick_week["weeks"]:
            # loop through the weeks
            name = w["name"]
            if "Term" in name:
                # normal term week
                # reset week counter and set term and week
                week_delta = 0
                term, week = name.split(", ")
                term_num = int(term.split(" ")[-1])
                week_num = int(week.split(" ")[-1])
            elif w["weekNumber"] <= 0:
                # welcome week or weeks before
                week_delta = 0
                term_num = 1
                week_num = int(w["weekNumber"])
            else:
                # holiday week so add 1 week
                week_delta += 1

            week_start_date = get_date_from_string(w["start"])
            if isinstance(week_start_date, str):
                return None
            week_end_date = get_date_from_string(w["end"])
            if isinstance(week_end_date, str):
                return None
            week_end_date += timedelta(hours=23, minutes=59, seconds=59)

            if week_start_date <= date <= week_end_date:
                # if the date is within the week, create the week
                break

        week = Week(
            academic_year=year,
            term=term_num,  # type: ignore
            week=week_num + week_delta,  # type: ignore
            start_date=week_start_date,  # type: ignore
        )

        db.session.add(week)
        return week

    # otherwise use the old dates file
    with Path("events/olddates.json").open("r") as f:
        old_dates = load(f)
    for w in reversed(old_dates):
        week_start_date = get_date_from_string(w["date"])
        if isinstance(week_start_date, str):
            return None
        if week_start_date <= date:
            term_num = w["term"]
            delta = date - week_start_date
            # add 1 to make 1-indexed
            # apart from t1 which has welcome week
            week_num = delta.days // 7 + 1 if term_num > 1 else delta.days // 7
            week_start_date = week_start_date + timedelta(
                weeks=week_num - (1 if term_num > 1 else 0)
            )
            week = Week(
                academic_year=year,
                term=term_num,
                week=week_num,
                start_date=week_start_date,
            )

            db.session.add(week)
            return week
    return None


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
    end_times: list[datetime] | None,
    tags: list[str],
) -> list[Event] | str:
    """Create multiple events at once"""
    events = []  # the created events
    for start_time, end_time in zip(
        start_times, end_times or [None] * len(start_times)
    ):
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
            end_time,
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


def clean_weeks() -> None:
    """Clean weeks that are not associated with any events"""
    weeks = Week.query.all()
    for week in weeks:
        if not week.events:
            db.session.delete(week)

    db.session.commit()


def clean_tags() -> None:
    """Clean tags that are not associated with any events"""
    tags = Tag.query.all()
    for tag in tags:
        if not tag.events:  # type: ignore
            db.session.delete(tag)
    db.session.commit()


def get_event_by_id(event_id: int) -> Event | None:
    """Get an event by its ID"""
    return Event.query.filter_by(id=event_id).first()


def get_event_by_slug(year: int, term: int, week: int, slug: str) -> Event | None:
    """Get an event by slug"""
    return (
        Event.query.filter(
            Event.date.has(academic_year=year, term=term, week=week),
            Event.slug == slug,  # type: ignore
        )
    ).first()


def get_events_by_time(
    year: int, term: int | None = None, week: int | None = None, draft: bool = False
) -> list[Event]:
    """Get events in a specific timeframe"""

    query = Event.query.filter(Event.date.has(academic_year=year))

    if term is not None:
        query = query.filter(Event.date.has(term=term))

    if week is not None:
        query = query.filter(Event.date.has(week=week))

    if not draft:
        query = query.filter(Event.draft.is_(False))  # type: ignore

    # order by start_time, end_time, and name
    return query.order_by(Event.start_time, Event.end_time, Event.name).all()  # type: ignore


_KEEP = object()  # placeholder to leave the field unchanged


def edit_event(  # noqa: PLR0913
    id: int,
    name: str | object = _KEEP,
    description: str | object = _KEEP,
    draft: bool | object = _KEEP,
    location: str | object = _KEEP,
    location_url: str | object | None = _KEEP,
    icon: str | object | None = _KEEP,
    colour: str | object | None = _KEEP,
    start_time: datetime | object = _KEEP,
    duration: timedelta | object | None = _KEEP,
    end_time: datetime | object | None = _KEEP,
    tags: list[str] | object | None = _KEEP,
) -> Event | str:
    """
    Edit an existing event
    If field is set to None, it will be deleted
    If field is set to _KEEP, it will not be changed
    """

    event = get_event_by_id(id)
    if not event:
        return "Event not found"

    # update the event attributes if provided
    event.name = name if name is not _KEEP else event.name
    event.slug = name.lower().replace(" ", "-") if name is not _KEEP else event.slug  # type: ignore
    event.description = description if description is not _KEEP else event.description
    event.draft = draft if draft is not _KEEP else event.draft
    event.location = location if location is not _KEEP else event.location
    event.location_url = (
        location_url if location_url is not _KEEP else event.location_url
    )
    if icon is not _KEEP:
        event.icon = icon.lower() if icon is not None else event.icon  # type: ignore
    event.colour = colour if colour is not _KEEP else event.colour

    event.start_time = (
        start_time.astimezone(pytz.timezone("Europe/London"))  # type: ignore
        if start_time is not _KEEP
        else event.start_time
    )
    if end_time is not _KEEP:
        event.end_time = (
            end_time.astimezone(pytz.timezone("Europe/London"))  # type: ignore
            if end_time is not None
            else event.end_time
        )

    # if duration is provided, calculate end_time and verify it
    if duration is not _KEEP and duration is not None:
        calculated_end_time = event.start_time + duration  # type: ignore
        if event.end_time and event.end_time != calculated_end_time:
            return "End time does not match the duration"
        event.end_time = calculated_end_time

    # update the week associated with the event
    if start_time is not _KEEP or end_time is not _KEEP or duration is not _KEEP:
        event.date = get_week_from_date(event.start_time)  # type: ignore

    # validate the event
    if error := event.validate():
        return error

    # update tags if provided
    if tags is not _KEEP:
        # clear existing tags
        event.tags.clear()
        # check all tags exist, create if not
        for tag in tags:  # type: ignore
            tag = tag.lower()  # noqa: PLW2901
            tag_obj = Tag.query.filter_by(name=tag).first()
            if not tag_obj:
                tag_obj = Tag(name=tag)
                db.session.add(tag_obj)
            event.tags.append(tag_obj)

    # commit the changes to the database
    db.session.commit()
    clean_weeks()
    clean_tags()

    return event


def delete_event(event_id: int) -> bool | str:
    """Delete an event by its ID"""
    event = get_event_by_id(event_id)
    if not event:
        return "Event not found"

    db.session.delete(event)
    db.session.commit()
    clean_weeks()
    clean_tags()
    return True


def validate_colour(text_colour: str | None, hex_colour: str | None) -> str | None:
    """Validate the colour input"""

    # check if the colours match
    if text_colour == hex_colour:
        return None

    # if either colour is None, validation succeeds
    if text_colour is None or hex_colour is None:
        return None

    # attemp to convert text_colour to hex
    text_colour = get_hex_from_name(text_colour)
    if text_colour is None:
        return "Invalid colour name"

    # check if the converted text_colour matches the hex_colour
    if text_colour.lower() != hex_colour.lower():
        return "Colour name does not match hex code"

    return None


def get_hex_from_name(name: str) -> str | None:
    """Get the hex colour from a name"""
    return colours.get(name.lower(), None)


def get_name_from_hex(hex_colour: str) -> str | None:
    """Get the name of a colour from its hex code"""
    for name, hex_code in colours.items():
        if hex_code.lower() == hex_colour.lower():
            return name
    return None


def get_all_tags() -> list[Tag]:
    """Get all tags from the database"""
    return Tag.query.order_by(Tag.name).all()


def get_events_by_tag(tag_name: str) -> list[Event]:
    """Get all events associated with a tag"""
    tag = Tag.query.filter_by(name=tag_name.lower()).first()
    if not tag:
        return []

    return tag.events


def get_tags_by_string(search: str, limit: int = 10) -> list[Tag]:
    """get tags by a string query"""
    search = search.lower()
    query = Tag.query.filter(Tag.name.ilike(f"%{search}%")).order_by(Tag.name)  # type: ignore

    return query.limit(limit).all() if limit != -1 else query.all()
