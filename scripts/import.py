# imports all the events from the old website and adds them to the new one via the API

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import parsedatetime
import pytz
import requests
import tomllib

from config import warwick_weeks

api_key = os.getenv("API_KEY")
base_url = "http://127.0.0.1:5000/api/events/"
events_folder = Path("scripts/archive")
tags_file = "scripts/tags.txt"
tags = {}
error_files = []
error_file = "scripts/errors.txt"


def get_date_from_week(year: str, term: str, week: str) -> date | None:
    """Get date from week"""

    # parse input
    parsed_year = int("20" + year[:2])
    parsed_term = int(term[1])
    parsed_week = int(week[1:])

    # get week from cache
    weeks = warwick_weeks[parsed_year - 2006]["weeks"]

    # find week
    inferred_weeks = []  # list of intermediary weeks
    current_term = None
    current_week = None

    for w in weeks:
        # extract core info
        name = w["name"]
        start = (
            datetime.strptime(w["start"], "%Y-%m-%d")
            .replace(tzinfo=pytz.timezone("Europe/London"))
            .date()
        )

        if "Term" in name:
            # extract week and term if standard week
            try:
                parts = name.split(", ")
                current_term = int(parts[0].split(" ")[1])
                current_week = int(parts[1].split(" ")[1])
                inferred_weeks.append((current_term, current_week, start))
            except (IndexError, ValueError):
                continue
        elif name == "Easter vacation, w/c Mon 15ᵗʰ Apr 2024":
            # w0 revision session (cs241)
            inferred_weeks.append((3, 0, start))
        elif name == "Summer vacation, w/c Mon 30ᵗʰ Jun 2025":
            # w11 online fng
            inferred_weeks.append((3, 11, start))
        elif w.get("weekNumber") == 0:
            # welcome week
            inferred_weeks.append((1, 0, start))

    # sort weeks by term and week number
    inferred_weeks.sort(key=lambda x: x[2])

    # fill in the weeks
    inferred_timeline = {}
    for i, (term_num, week_num, start_date) in enumerate(inferred_weeks):
        # set the start date for the week
        inferred_timeline[(term_num, week_num)] = start_date

        if i + 1 < len(inferred_weeks):
            # get the next one
            next_start = inferred_weeks[i + 1][2]
            # fill in the weeks between
            weeks_between = (next_start - start_date).days // 7
            for j in range(1, weeks_between):
                inferred_timeline[(term_num, week_num + j)] = start_date + timedelta(
                    weeks=j
                )

    if (parsed_term, parsed_week) in inferred_timeline:
        return inferred_timeline[(parsed_term, parsed_week)]

    known_weeks = [week for (term, week) in inferred_timeline if term == parsed_term]

    closest_week = max(
        [week for week in known_weeks if week < parsed_week], default=None
    )
    if closest_week is not None:
        base_date = inferred_timeline[(parsed_term, closest_week)]
        delta = parsed_week - closest_week
        return base_date + timedelta(weeks=delta)

    return None


def get_date_time(date_str: str, path: Path) -> datetime:
    """Get datetime from string :wah:"""
    try:
        # attempt to parse as ISO-8601 format
        return datetime.fromisoformat(date_str).astimezone(
            pytz.timezone("Europe/London")
        )
    except ValueError:
        # if that fails, use custom parsing
        base_date = get_date_from_week(path.parts[2], path.parts[3], path.parts[4])
        time, _ = parsedatetime.Calendar().parseDT(
            date_str, base_date, pytz.timezone("Europe/London")
        )
        # if time is a week ahead of the base date (on mon), subtract a week from time
        # yes i know this is a hack, cope
        if time.date() >= base_date + timedelta(weeks=1):  # type: ignore
            print(f"Time is adjusted for {path} in {path.parts[4]}")
            time -= timedelta(weeks=1)
        return time


def parse_event(path: Path, repeat: bool) -> dict:
    """Parse an event and return it as a dictionary."""

    with path.open("rb") as f:
        content = f.read().decode("utf-8")

    # divided by +++ lines
    parts = content.split("+++")
    if len(parts) < 3:  # noqa: PLR2004
        raise ValueError(f"Invalid TOML file format: {path}")

    # load event data and flatten
    event = tomllib.loads(parts[1].strip())
    event.update(event.pop("extra", {}))
    event.update(event.pop("taxonomies", {}))

    # add description
    event["description"] = parts[2].strip() if parts[2].strip() else event["title"]

    if not repeat:
        # parse start time
        start_time = get_date_time(event["date"], path)
        event["start_time"] = start_time

        # parse end time if supplied
        if "end_time" in event:
            try:
                # attempt to parse as ISO-8601 format
                event["end_time"] = datetime.fromisoformat(
                    event["end_time"]
                ).astimezone(pytz.timezone("Europe/London"))
            except ValueError:
                # if that fails, use custom parsing
                time, _ = parsedatetime.Calendar().parseDT(
                    event["end_time"],
                    event["start_time"],
                    pytz.timezone("Europe/London"),
                )
                event["end_time"] = time

            # error handling
            if event["end_time"] < event["start_time"]:
                raise ValueError(
                    f"End ({event["end_time"]}) is before start ({event["start_time"]})"
                )

    # process icon to convert icons/<icon>.svg to <icon>
    if "icon" in event:
        event["icon"] = event["icon"].removeprefix("icons/").removesuffix(".svg")

    return event


def add_event(file: Path, event: dict) -> None:  # noqa: PLR0912
    """Add an event to the API"""

    # create colour and icon if not present
    if "colour" not in event:
        if "gaming" in event["title"].lower():
            event["colour"] = "gaming"
            event["icon"] = "fng" if not event.get("icon") else event["icon"]
        if "social" in event["title"].lower():
            event["colour"] = "social"
        if any(word in event["location"].lower() for word in ["duck", "coach"]):
            event["colour"] = "social"
            event["icon"] = "ph-hamburger" if not event.get("icon") else event["icon"]

    # prepare event and send to API
    event_json = {
        "name": event["title"],
        "description": event["description"],
        "location": event["location"],
        "start_time": event["start_time"].strftime("%Y-%m-%dT%H:%M"),
    }
    if "draft" in event:
        event_json["draft"] = event["draft"]
    if "location_url" in event:
        event_json["location_url"] = event["location_url"]
    if "icon" in event:
        event_json["icon"] = event["icon"]
    if "colour" in event:
        event_json["colour"] = event["colour"]
    if "end_time" in event:
        event_json["end_time"] = event["end_time"].strftime("%Y-%m-%dT%H:%M")

    response = requests.post(
        base_url + "create/",
        json=event_json,
        headers={"Authorization": api_key},
        timeout=50,
    )

    if response.status_code == 201:  # noqa: PLR2004
        print(f"Successfully imported {file}")
    else:
        # try again just in case
        response = requests.post(
            base_url + "create/",
            json=event_json,
            headers={"Authorization": api_key},
            timeout=50,
        )
        if response.status_code == 201:  # noqa: PLR2004
            print(f"Successfully imported {file} on retry")
        else:
            print(f"Failed to import {file}: {response.text.replace('\n', ' ')}")
            error_files.append((file, response.text.replace("\n", " ")))

    event_id = response.json().get("id", None)
    if not event_id:
        return

    # add tags to list for sorting later
    if "tags" in event:
        event_tags = event.pop("tags")
        for tag in event_tags:
            if tag not in tags:
                # if tag doesn't exist, create it
                tags[tag] = [str(event_id)]
            else:
                # otherwise, append to existing tag
                tags[tag].append(str(event_id))


def import_events() -> None:
    """Import events from the archive folder and add them to the new API"""

    print("Importing events...")
    # loop over all events
    for file in events_folder.rglob("*.md"):
        print(f"Importing {file}...")

        try:
            # create base event dict
            event = parse_event(file, "repeat" in file.parts)
        except ValueError as e:
            print(f"Error parsing {file}: {e}")
            error_files.append((file, str(e)))
            continue

        if "repeat" in file.parts:
            # if repeat, add an event for each week
            for week in event["weeks"]:
                event_copy = event.copy()
                # date parsing
                event_date = get_date_from_week(file.parts[2], file.parts[3], week)
                time, _ = parsedatetime.Calendar().parseDT(
                    event["date"], event_date, pytz.timezone("Europe/London")
                )
                # same hack to subtract a week if necessary
                if time.date() >= event_date + timedelta(weeks=1):  # type: ignore
                    print(f"Time is adjusted for {file} in {week}")
                    time -= timedelta(weeks=1)
                event_copy["start_time"] = time
                if "end_time" in event_copy:
                    time, _ = parsedatetime.Calendar().parseDT(
                        event["end_time"],
                        event_copy["start_time"],
                        pytz.timezone("Europe/London"),
                    )
                    event_copy["end_time"] = time
                add_event(file, event_copy)
        else:
            add_event(file, event)

    # write tags to file
    with Path(tags_file).open("w", encoding="utf-8") as f:
        f.writelines(f"{tag}:{','.join(events)}\n" for tag, events in tags.items())

    # if error, write them
    if error_files:
        with Path(error_file).open("w", encoding="utf-8") as f:
            f.writelines(f"{file}: {error}\n" for file, error in error_files)

    print("done :)")


def import_tags() -> None:
    """Import tags from tags file and add to API"""
    # reverse dictionary to get tags for each event
    event_tags = {}
    print("Importing tags file")
    with Path(tags_file).open("r", encoding="utf-8") as f:
        for line in f:
            tag, events = line.strip().split(":")
            for event in events.split(","):
                if event not in event_tags:
                    event_tags[event] = []
                event_tags[event].append(tag)
    print("Tags imported")

    print("Adding tags to API")
    for event, tags in event_tags.items():
        print(f"Processing {event} with tags {", ".join(tags)}")

        # add tags to event
        response = requests.patch(
            base_url + event + "/",
            json={"tags": tags},
            headers={"Authorization": api_key},
            timeout=50,
        )

        if response.status_code == 200:  # noqa: PLR2004
            print(f"Successfully added tags to {event}")
        else:
            print(f"Failed to add tags to {event}: {response.text}")
            error_files.append((event, response.text.replace("\n", " ")))


if __name__ == "__main__":
    start = datetime.now()  # noqa: DTZ005

    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg == "import":
        import_events()
    elif arg == "tags":
        import_tags()

    print("Finished in", datetime.now() - start)  # noqa: DTZ005
