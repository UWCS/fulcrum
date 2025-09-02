import base64
from pathlib import Path

import svg

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


def create_single_week(events: list[dict], week: Week) -> list[svg.Element]:
    elements = []
    elements.append(
        svg.Path(
            d=phosphor_icon_paths["calendar"],
            transform=[svg.Scale(0.5), svg.Translate(500, 500)],
        )
    )
    elements.append(
        svg.Text(
            text=f"Week {week.week}",
            x=500,
            y=100,
            class_=["title"],
            font_size=50,
            text_anchor="middle",
        )
    )
    elements.append(
        svg.Text(
            text=f"Term {week.term}, Academic Year {week.academic_year}",
            x=500,
            y=160,
            class_=["text"],
            font_size=30,
            text_anchor="middle",
        )
    )
    return elements


def create_multi_week(events: list[dict], start: Week, end: Week) -> list[svg.Element]:
    elements = []
    elements.append(
        svg.Path(
            d=phosphor_icon_paths["calendar-dots"],
            transform=[svg.Scale(0.5), svg.Translate(500, 500)],
        )
    )
    elements.append(
        svg.Text(
            text=f"Weeks {start.week} - {end.week}",
            x=500,
            y=100,
            class_=["title"],
            font_size=50,
            text_anchor="middle",
        )
    )
    elements.append(
        svg.Text(
            text=f"Term {start.term}, Academic Year {start.academic_year}",
            x=500,
            y=160,
            class_=["text"],
            font_size=30,
            text_anchor="middle",
        )
    )
    return elements


def get_b64_font(path: str) -> str:
    with Path(path).open("rb") as f:
        bytes = f.read()
    encoded = base64.b64encode(bytes).decode("utf-8")
    return f"data:font/woff2;base64,{encoded}"


def create_svg(start: Week, end: Week) -> str:
    """Create publicity SVG calenndar for events between two weeks (inclusive)"""

    montserrat_500 = get_b64_font("static/fonts/montserrat-v26-latin-500.woff2")
    montserrat_600 = get_b64_font("static/fonts/montserrat-v26-latin-600.woff2")

    elements: list[svg.Element] = [
        svg.Style(
            text=f"""
                @font-face {{
                    font-family: 'montserrat-bold';
                    src: url({montserrat_600}) format('woff2');
                }}

                .title {{
                    font-family: 'montserrat-bold';
                    font-weight: 600;
                }}

                @font-face {{
                    font-family: 'montserrat-semibold';
                    src: url({montserrat_500}) format('woff2');
                }}

                .text {{
                    font-family: 'montserrat-semibold';
                    font-weight: 500;
                }}
            """
        )
    ]

    events = get_events(start, end)
    if start == end:
        elements.extend(create_single_week(events, start))
    else:
        elements.extend(create_multi_week(events, start, end))

    return str(svg.SVG(elements=elements, viewBox=svg.ViewBoxSpec(0, 0, 1000, 1000)))
