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


base_svg = [
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 1000'>",
    "<style>",
    "@font-face { font-family: 'monsterrat-bold'; src: url(https://fonts.gstatic.com/s/montserrat/v30/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCu173w3aXpsog.woff2) format('woff2'); }",  # noqa: E501
    ".title { font-family: 'monsterrat-bold'; font-weight: 700; }",
    "@font-face { font-family: 'monsterrat-semibold'; src: url(https://fonts.gstatic.com/s/montserrat/v30/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCuM73w5aXo.woff2) format('woff2'); }",  # noqa: E501
    ".text { font-family: 'monsterrat-semibold'; font-weight: 600; }",
    "</style>",
]


def create_single_week(events: list[dict], week: Week) -> list[str]:
    svg = base_svg.copy()
    svg.append(f"<path d='{phosphor_icon_paths["calendar"]}' scale='0.5'/>")
    svg.append(
        f"<text x='500' y='100' text-anchor='middle' class='title' font-size='50'>Week {week.week}</text>"  # noqa: E501
    )
    svg.append(
        f"<text x='500' y='160' text-anchor='middle' class='text' font-size='30'>Term {week.term}, Academic Year {week.academic_year}</text>"  # noqa: E501
    )
    return svg


def create_multi_week(events: list[dict], start: Week, end: Week) -> list[str]:
    svg = base_svg.copy()
    svg.append(f"<path d='{phosphor_icon_paths["calendar-dots"]}' scale='0.5'/>")
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
