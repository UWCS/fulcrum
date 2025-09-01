import json
import re
from datetime import datetime
from pathlib import Path

import pytz
import requests

# custom colours
colours = {
    "blue": "#3A7DFF",
    "yellow": "#FFC700",
    "grey": "#202429",
    "greyer": "#2F3338",
    "external": "#989898",
    "president": "#FDD835",
    "gaming": "#3D53FF",
    "treasurer": "#FD6035",
    "welfare": "#4F33DB",
    "gaming2": "#8135FD",
    "academic": "#EE4F4F",
    "tech": "#0EAD57",
    "secretary": "#1DC9FF",
    "social": "#B53DFF",
    "inclusivity": "#24D09D",
    "publicity": "#EF8A2C",
    "events": "#1DC9FF",
    "sports": "#B53DFF",
    "compcafe": "#358A4D",
    "milk": "#4BB3FF",
}

# custom icons from static/icons directory
custom_icons = [
    f.stem for f in Path("static/icons").iterdir() if f.is_file() and f.suffix == ".svg"
]

# load all phosphor icons from CSS file
phosphor_icons = sorted(
    set(
        re.findall(
            r"\.ph-bold\.ph-([a-z0-9-]+):before",
            Path("static/icons/phosphor-bold.css").read_text(),
        )
    )
)

icons = sorted(custom_icons + phosphor_icons)

# the new campus map API requires auth so commenting this out for now
# logic remains for future use
# mapping of common location names to their canonical names
# mapping also exists in static/js/event-management.js if updating
# room_mapping = {
#     "mb001": "Computer Science Teaching Room",
#     "sports hub": "Sports and Wellbeing Hub",
#     "dcs": "Computer Science",
#     "cs dept": "Computer Science",
#     "dcs atrium": "Computer Science",
#     "computer science dept": "Computer Science",
#     "computer science department": "Computer Science",
#     "department of computer science": "Computer Science",
#     "junction hall 1": "jx003",
#     "junction hall 2": "jx010",
# }

# categories duplicated (+ other at templates/events/macros/filter.html)
categories = ["gaming", "academic", "social", "inclusivity", "tech"]

# get warwick weeks from API and cache for later use
# +5 years for future proofing
# note, this requires the app to be restarted every 5 years
# (however given the current state of UWCS uptime, this is guaranteed to happen)
_now = datetime.now(tz=pytz.timezone("Europe/London"))
_academic_year = _now.year if _now.month <= 9 else _now.year + 1  # noqa: PLR2004
try:
    warwick_weeks = [
        requests.get(
            f"https://tabula.warwick.ac.uk/api/v1/termdates/{year}/weeks?numberingSystem=term",
            timeout=5,
        ).json()
        for year in range(2006, _academic_year + 5)
    ]
except requests.RequestException as error:
    raise SystemExit("Could not connect to warwick API aborting") from error

old_dates = [
    {"academicYear": 2001, "term": 1, "date": "2001-09-24"},
    {"academicYear": 2001, "term": 2, "date": "2002-01-07"},
    {"academicYear": 2001, "term": 3, "date": "2002-04-22"},
    {"academicYear": 2002, "term": 1, "date": "2002-09-23"},
    {"academicYear": 2002, "term": 2, "date": "2003-01-06"},
    {"academicYear": 2002, "term": 3, "date": "2003-04-21"},
    {"academicYear": 2003, "term": 1, "date": "2003-09-22"},
    {"academicYear": 2003, "term": 2, "date": "2004-01-05"},
    {"academicYear": 2003, "term": 3, "date": "2004-04-19"},
    {"academicYear": 2004, "term": 1, "date": "2004-09-20"},
    {"academicYear": 2004, "term": 2, "date": "2005-01-03"},
    {"academicYear": 2004, "term": 3, "date": "2005-04-18"},
    {"academicYear": 2005, "term": 1, "date": "2005-09-19"},
    {"academicYear": 2005, "term": 2, "date": "2006-01-02"},
    {"academicYear": 2005, "term": 3, "date": "2006-04-17"},
]

# icon paths for phosphor icons (used when creating SVGs)
phosphor_icon_paths = json.loads(Path("icons.json").read_text())
