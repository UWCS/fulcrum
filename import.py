# imports all the events from the old website and adds them to the new one via the API

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import parsedatetime
import pytz
import requests
import tomllib

api_key = "testing"
base_url = "http://127.0.0.1:5000/api/events/"
events_folder = Path("archive")
tags_file = "tags.csv"
tags = {}
error_files = []
error_file = "errors.txt"


def get_date_from_week(year: str, term: str, week: str) -> date | None:
    """Get date from week"""

    # parse input
    parsed_year = int("20" + year[:2])
    parsed_term = int(term[1])
    parsed_week = int(week[1:])

    # make request to api
    try:
        weeks = requests.get(
            f"https://tabula.warwick.ac.uk/api/v1/termdates/{parsed_year}/weeks?numberingSystem=term",
            timeout=50,  # api can be tempremental
        ).json()["weeks"]
    except Exception as e:
        raise ValueError("Unable to get dates from API") from e

    inferred_weeks = []
    current_term = None
    current_week = None

    for w in weeks:
        name = w["name"]
        start = (
            datetime.strptime(w["start"], "%Y-%m-%d")
            .replace(tzinfo=pytz.timezone("Europe/London"))
            .date()
        )

        if "Term" in name:
            try:
                parts = name.split(", ")
                current_term = int(parts[0].split(" ")[1])
                current_week = int(parts[1].split(" ")[1])
                inferred_weeks.append((current_term, current_week, start))
            except (IndexError, ValueError):
                continue
        elif w.get("weekNumber") == 0:
            inferred_weeks.append((1, 0, start))

    inferred_weeks.sort(key=lambda x: x[2])  # sort by date

    inferred_timeline = {}

    for i, (term_num, week_num, start_date) in enumerate(inferred_weeks):
        inferred_timeline[(term_num, week_num)] = start_date

        if i + 1 < len(inferred_weeks):
            next_start = inferred_weeks[i + 1][2]
            weeks_between = (next_start - start_date).days // 7
            for j in range(1, weeks_between):
                inferred_timeline[(term_num, week_num + j)] = start_date + timedelta(
                    weeks=j
                )

    return inferred_timeline.get((parsed_term, parsed_week), None)


def get_date_time(date_str: str, path: Path) -> datetime:
    """Get datetime from string :wah:"""
    try:
        # attempt to parse as ISO-8601 format
        return datetime.fromisoformat(date_str).astimezone(
            pytz.timezone("Europe/London")
        )
    except ValueError:
        # if that fails, use custom parsing
        base_date = get_date_from_week(path.parts[1], path.parts[2], path.parts[3])
        time, _ = parsedatetime.Calendar().parseDT(
            date_str, base_date, pytz.timezone("Europe/London")
        )
        return time


def parse_event(path: Path) -> dict:
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

    # parse start time
    start_time = get_date_time(event["date"], path)
    event["start_time"] = start_time

    # parse end time if supplied
    if "end_time" in event:
        try:
            # attempt to parse as ISO-8601 format
            event["end_time"] = datetime.fromisoformat(event["end_time"]).astimezone(
                pytz.timezone("Europe/London")
            )
        except ValueError:
            # if that fails, use custom parsing
            time, _ = parsedatetime.Calendar().parseDT(
                event["end_time"], event["start_time"], pytz.timezone("Europe/London")
            )
            event["end_time"] = time

        if event["end_time"] < event["start_time"]:
            raise ValueError(
                f"End ({event["end_time"]}) is before start ({event["start_time"]})"
            )

    # process icon to convert icons/<icon>.svg to <icon>
    if "icon" in event:
        event["icon"] = event["icon"].removeprefix("icons/").removesuffix(".svg")

    return event


def import_events() -> None:  # noqa: PLR0912
    """Import events from the archive folder and add them to the new API"""

    print("Importing events...")
    for file in events_folder.rglob("*.md"):
        print(f"Importing {file}...")

        try:
            if "repeat" in str(file.parent):
                # skip for now
                continue
            else:
                event = parse_event(file)
        except Exception as e:
            print(f"Error parsing {file}: {e}")
            error_files.append((file, str(e)))
            continue

        # tags processing
        if "tags" in event:
            event_tags = event.pop("tags")
            for tag in event_tags:
                if tag not in tags:
                    # if tag doesnt exist, create it
                    tags[tag] = [event["title"]]
                else:
                    # otherwise, append to existing tag
                    tags[tag].append(event["title"])

        # create colour
        if "colour" not in event:
            if "gaming" in event["title"].lower():
                event["colour"] = "gaming"
                event["icon"] = "fng"
            if "social" in event["title"].lower():
                event["colour"] = "social"
            if any(word in event["location"].lower() for word in ["duck", "coach"]):
                event["colour"] = "social"
                event["icon"] = "hamburger"

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
            timeout=5,
        )

        if response.status_code == 201:  # noqa: PLR2004
            print(f"Successfully imported {file}")
        else:
            print(f"Failed to import {file}: {response.text.replace("\n", " ")}")
            error_files.append((file, response.text))

    # write tags to file
    with Path(tags_file).open("w", encoding="utf-8") as f:
        f.writelines(f"{tag}:{','.join(events)}\n" for tag, events in tags.items())

    if error_files:
        with Path(error_file).open("w", encoding="utf-8") as f:
            f.writelines(f"{file}: {error}\n" for file, error in error_files)

    print("done :)")


if __name__ == "__main__":
    start = datetime.now()  # noqa: DTZ005

    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg == "import":
        import_events()

    print("Finished in", datetime.now() - start)  # noqa: DTZ005
