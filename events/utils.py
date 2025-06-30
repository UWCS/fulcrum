from datetime import datetime, timedelta
from json import load
from pathlib import Path

import pytz
import requests

from config import colours
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

    # convert icon to lowercase
    icon = icon.lower() if icon else None

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

    # add the event to db to allow tags
    db.session.add(event)

    # attach tags to the event
    # check all tags exist, create if not
    for tag in tags:
        tag_obj = Tag.query.filter_by(name=tag).first()
        if not tag_obj:
            tag_obj = Tag(name=tag)
            db.session.add(tag_obj)
        event.tags.append(tag_obj)

    db.session.commit()

    return event


def get_week_from_date(date: datetime) -> Week | None:  # noqa: PLR0912
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
                f"https://tabula.warwick.ac.uk/api/v1/termdates/{year}/weeks?numberingSystem=term",
                timeout=5,
            ).json()

            week_delta = 0
            for w in reversed(warwick_week["weeks"]):
                start_date = get_date_from_string(w["start"])
                if isinstance(start_date, str):
                    return None
                if start_date <= date:
                    name = w["name"]
                    if "Term" in name:
                        parts = name.split(", ")
                        term_num = int(parts[0].split(" ")[-1])
                        week_num = int(parts[1].split(" ")[-1])
                    elif w["weekNumber"] == 0:
                        # welcome week
                        term_num = 1
                        week_num = 0
                    else:
                        week_delta += 1
                        continue

                    start_date = start_date + timedelta(weeks=week_delta)
                    week = Week(
                        academic_year=year,
                        term=term_num,
                        week=week_num + week_delta,
                        start_date=start_date,
                    )

                    db.session.add(week)
                    db.session.commit()
                    break
        else:
            with Path("olddates.json").open("r") as f:
                old_dates = load(f)
            for w in reversed(old_dates["weeks"]):
                start_date = get_date_from_string(w["date"])
                if isinstance(start_date, str):
                    return None
                if start_date <= date:
                    term_num = w["term"]
                    delta = date - start_date
                    # add 1 to make 1-indexed
                    # apart from t1 which has welcome week
                    week_num = delta.days // 7 + 1 if term_num > 1 else delta.days // 7
                    start_date = start_date + timedelta(
                        weeks=week_num - (1 if term_num > 1 else 0)
                    )
                    week = Week(
                        academic_year=year,
                        term=term_num,
                        week=week_num,
                        start_date=start_date,
                    )
                    db.session.add(week)
                    db.session.commit()

    return week


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


def edit_event(  # noqa: PLR0913
    id: int,
    name: str | None = None,
    description: str | None = None,
    draft: bool | None = None,
    location: str | None = None,
    location_url: str | None = None,
    icon: str | None = None,
    colour: str | None = None,
    start_time: datetime | None = None,
    duration: timedelta | None = None,
    end_time: datetime | None = None,
    tags: list[str] | None = None,
) -> Event | str:
    """Edit an existing event"""

    event = get_event_by_id(id)
    if not event:
        return "Event not found"

    # update the event attributes if provided
    event.name = name if name is not None else event.name
    event.slug = name.lower().replace(" ", "-") if name else event.slug
    event.description = description if description is not None else event.description
    event.draft = draft if draft is not None else event.draft
    event.location = location if location is not None else event.location
    event.location_url = (
        location_url if location_url is not None else event.location_url
    )
    event.icon = icon.lower() if icon else event.icon
    event.colour = colour if colour else event.colour
    event.start_time = (
        start_time.astimezone(pytz.timezone("Europe/London"))
        if start_time
        else event.start_time
    )
    event.end_time = (
        end_time.astimezone(pytz.timezone("Europe/London"))
        if end_time
        else event.end_time
    )

    # if duration is provided, calculate end_time and verify it
    if duration:
        calculated_end_time = event.start_time + duration
        if event.end_time and event.end_time != calculated_end_time:
            return "End time does not match the duration"
        event.end_time = calculated_end_time

    # update the week associated with the event
    event.date = get_week_from_date(event.start_time)  # type: ignore

    # validate the event
    if error := event.validate():
        return error

    # update tags if provided
    if tags is not None:
        # clear existing tags
        event.tags.clear()
        # check all tags exist, create if not
        for tag in tags:
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


def get_tags_by_string(search: str, limit: int = 10) -> list[Tag]:
    """get tags by a string query"""
    search = search.lower()
    query = Tag.query.filter(Tag.name.ilike(f"%{search}%")).order_by(Tag.name)  # type: ignore

    return query.limit(limit).all() if limit != -1 else query.all()
