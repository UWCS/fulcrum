import svg

from config import colours
from exec.calendar.config import (
    NUM_WEEKS,
    POST_HEIGHT,
    POST_WIDTH,
    TERM_CONTENT_HEIGHT,
    TERM_DAY_SIZE,
    TERM_DAY_TEXT_HEIGHT,
    TERM_DAY_TEXT_SIZE,
    TERM_PADDING_X,
    TERM_TITLE_SIZE,
    TERM_WEEK_PADDING,
    TERM_WEEK_RADIUS,
    WEEK_NUM_SIZE,
    WEEK_NUM_WIDTH,
)
from exec.calendar.renderer.day import create_day_circle
from schema import Week


def create_multi_week(
    events: list[dict], start: Week, end: Week, for_figma: bool
) -> list[svg.Element]:
    """Create the calendar 5 weeks"""

    if end.week - start.week + 1 != NUM_WEEKS:
        raise ValueError("Can only create 5 week calendars")

    # add base title
    elements: list[svg.Element] = [
        svg.Text(
            text=f"Term {start.term} Calendar",
            x=POST_HEIGHT / 2,
            y=POST_HEIGHT / 4.2,
            font_size=TERM_TITLE_SIZE,
            text_anchor="middle",
            class_=["title"],
        )
    ]

    # calculate sizings
    term_height = TERM_CONTENT_HEIGHT
    term_width = POST_WIDTH * (1 - 2 * TERM_PADDING_X)
    term_top = POST_HEIGHT - TERM_CONTENT_HEIGHT
    term_left = POST_WIDTH * TERM_PADDING_X

    week_height = (
        term_height - TERM_DAY_TEXT_HEIGHT - (NUM_WEEKS + 1) * (TERM_WEEK_PADDING * term_height)
    ) / NUM_WEEKS
    week_width = term_width

    # add week days
    day_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
    day_size = week_height * TERM_DAY_SIZE
    day_names_base = term_left + WEEK_NUM_WIDTH * term_width + day_size / 2
    for i, day in enumerate(day_names):
        elements.append(
            svg.Text(
                text=day,
                x=day_names_base + i * day_size,
                y=term_top + TERM_DAY_TEXT_HEIGHT,
                font_size=TERM_DAY_TEXT_SIZE,
                text_anchor="middle",
                class_=["title"],
            )
        )

    # add week events
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    week_base = term_top + TERM_DAY_TEXT_HEIGHT + TERM_WEEK_PADDING * term_height
    text_base = week_base + week_height / 2
    for i, week in enumerate(events[0]["terms"][0]["weeks"]):
        elements.extend(
            [
                # rectangle background
                svg.Rect(
                    x=term_left,
                    y=week_base + i * (week_height + TERM_WEEK_PADDING * term_height),
                    width=week_width,
                    height=week_height,
                    fill=colours["greyer"],
                    rx=TERM_WEEK_RADIUS,
                    ry=TERM_WEEK_RADIUS,
                ),
                # week num
                svg.Text(
                    text=str(week["week"]),  # str to stop week 0 not being rendered
                    x=term_left + (WEEK_NUM_WIDTH * term_width) / 2,
                    y=(
                        text_base
                        + i * (week_height + TERM_WEEK_PADDING * term_height)
                        + (week_height / 7.5 if for_figma else 0)
                    ),
                    font_size=WEEK_NUM_SIZE,
                    text_anchor="middle",
                    dominant_baseline="middle",
                    class_=["title"],
                ),
            ]
        )

        # convert days into a single dictionary
        day_map = {day["day"]: day for day in week["days"]}
        all_days = [day_map.get(day, {"day": day, "events": []}) for day in day_names]

        # add events in each day
        for j, day in enumerate(all_days):
            day_circle = create_day_circle(day["events"], day_size, for_figma)
            day_circle.transform = [
                svg.Translate(
                    day_names_base + j * day_size,
                    text_base + i * (week_height + TERM_WEEK_PADDING * term_height),
                )
            ]
            elements.append(day_circle)

    return elements
