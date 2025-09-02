import base64
from pathlib import Path

from config import phosphor_icon_paths
from events.utils import get_events_in_week_range, group_events
from schema import Week


def get_events(start: Week, end: Week) -> list[dict]:
    """Get events between two weeks (inclusive)"""

    if start.academic_year != end.academic_year:
        raise ValueError("Start and end week must be in the same academic year")
    if start.term != end.term:
        raise ValueError("Start and end week must be in the same term")
    if start.week > end.week:
        raise ValueError("Start week must be before or equal to end week")

    events = get_events_in_week_range(start, end)

    return group_events(events)


def get_b64_font(path: str) -> str:
    with Path(path).open("rb") as f:
        bytes = f.read()
    encoded = base64.b64encode(bytes).decode("utf-8")
    return f"data:font/woff2;base64,{encoded}"


montserrat_500 = get_b64_font("static/fonts/montserrat-v26-latin-500.woff2")
montserrat_600 = get_b64_font("static/fonts/montserrat-v26-latin-600.woff2")


base_svg = [
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 1000'>",
    "<style>",
    f"@font-face {{ font-family: 'monsterrat-bold'; src: url({montserrat_600}) format('woff2'); }}",  # noqa: E501
    ".title { font-family: 'monsterrat-bold'; font-weight: 600; }",
    f"@font-face {{ font-family: 'monsterrat-semibold'; src: url({montserrat_500}) format('woff2'); }}",  # noqa: E501
    ".text { font-family: 'monsterrat-semibold'; font-weight: 500; }",
    "</style>",
]


def create_single_week(events: list[dict], week: Week) -> list[str]:
    svg = base_svg.copy()
    svg.append(
        f"<path d='{phosphor_icon_paths["calendar"]}' transform='scale(0.5) translate(500, 500)'/>"  # noqa: E501
    )
    svg.append(
        f"<text x='500' y='100' text-anchor='middle' class='title' font-size='50'>Week {week.week}</text>"  # noqa: E501
    )
    svg.append(
        f"<text x='500' y='160' text-anchor='middle' class='text' font-size='30'>Term {week.term}, Academic Year {week.academic_year}</text>"  # noqa: E501
    )
    return svg


def create_multi_week(events: list[dict], start: Week, end: Week) -> list[str]:
    svg = base_svg.copy()
    svg.append(
        f"<path d='{phosphor_icon_paths["calendar-dots"]}' transform='scale(0.5) translate(500, 500)'/>"  # noqa: E501
    )
    svg.append(
        f"<text x='500' y='100' text-anchor='middle' class='title' font-size='50'>Weeks {start.week} - {end.week}</text>"  # noqa: E501
    )
    svg.append(
        f"<text x='500' y='160' text-anchor='middle' class='text' font-size='30'>Term {start.term}, Academic Year {start.academic_year}</text>"  # noqa: E501
    )
    return svg


def create_svg(start: Week, end: Week) -> str:
    """Create publicity SVG calenndar for events between two weeks (inclusive)"""

    events = get_events(start, end)

    if start == end:
        svg = create_single_week(events, start)
    else:
        svg = create_multi_week(events, start, end)

    return "\n".join([*svg, "</svg>"])
