import svg

from config import colours
from exec.calendar.config import (
    CELL_PADDING,
    CELL_RADIUS,
    DAY_TEXT_HEIGHT,
    DAY_TEXT_SIZE,
    POST_HEIGHT,
    POST_WIDTH,
    WEEK_TITLE_SIZE,
)
from exec.calendar.layout import get_event_groups
from exec.calendar.renderer.event import get_event_circle
from exec.calendar.svg_utils import get_socials
from schema import Week


def create_single_week(  # noqa: PLR0912, PLR0915
    events: list[dict], week: Week
) -> list[svg.Element]:
    """Create the calendar for a single week"""

    elements: list[svg.Element] = [
        # add week text
        svg.Text(
            text=f"Week {week.week}",
            x=POST_WIDTH / 2,
            y=POST_HEIGHT / 4,
            font_size=WEEK_TITLE_SIZE,
            text_anchor="middle",
            class_=["title"],
        ),
    ]

    # get the events for the week
    # find the list of weeks in the term
    try:
        term_weeks = events[0]["terms"][0]["weeks"]
    except (IndexError, KeyError):
        raise ValueError("No events found for this week") from None
    # because terms can start at negative weeks, have gaps, and use different indexing
    # loop over the weeks to find the correct one
    week_days = []
    for w in term_weeks:
        if w["week"] == week.week:
            week_days = w["days"]
            break

    # group events by day and create layout
    # calculate the number of events each day
    num_events = [len(day["events"]) for day in week_days]

    # if odd, add 1 (the social links) to make even so we can make perfect grid
    if sum(num_events) % 2 != 0:
        num_events.append(1)
        week_days.append({"day": "Socials", "events": []})

    # find best way to split events into groups
    shapes, grid = get_event_groups(num_events)

    # find size of grid
    num_rows, num_cols = len(grid), len(grid[0])

    # find position and sizing of grid
    grid_height = (POST_HEIGHT / 1.5) if num_rows < 3 else (POST_HEIGHT / 1.35)  # noqa: PLR2004
    grid_width = POST_WIDTH
    grid_top = POST_HEIGHT / 4 + (POST_HEIGHT - POST_HEIGHT / 4 - grid_height) / 2

    # sizing factors
    pull_factor = 0.2
    two_col_shrink_x = 0.7
    two_col_shrink_y = 0.5

    # find sizing of cells
    if num_cols == 2:  # noqa: PLR2004
        # if only two columns, shrink grid to make it look better
        grid_width *= two_col_shrink_x
        grid_left = (POST_WIDTH - grid_width) / 2
        if num_rows == 1:
            # if only one row, shrink vertically too
            orig_grid_height = grid_height
            grid_height *= two_col_shrink_y
            grid_top += (orig_grid_height - grid_height) / 2
    else:
        grid_left = 0
    cell_height = grid_height / num_rows
    cell_width = grid_width / num_cols
    padding_x = cell_width * (1 - CELL_PADDING) / 2
    padding_y = cell_height * (1 - CELL_PADDING) / 2

    for i, day_events in enumerate(week_days):
        # extract info from existing arrays
        day, day_event_list = day_events["day"], day_events["events"]
        row_width, col_width = shapes[i]

        # find position of cells in grid
        found = False
        base_row = base_col = 0
        for row in range(num_rows):
            for col in range(num_cols):
                if grid[row][col] == i:
                    base_row, base_col = row, col
                    found = True
                    break
            if found:
                break

        # calculate initial offset (top left of first cell)
        base_x = grid_left + base_col * cell_width
        base_y = grid_top + base_row * cell_height
        centre_y = base_y + col_width * cell_height / 2 + DAY_TEXT_HEIGHT / 2

        if day == "Socials":
            # apply socials box if necessary
            socials = get_socials(cell_width - 2 * padding_x, cell_height - 2 * padding_y)
            socials.transform = [svg.Translate(base_x + padding_x, base_y + padding_y)]
            elements.append(socials)
            continue

        # add background rectangle and day text
        elements.extend(
            [
                svg.Rect(
                    x=base_x + padding_x,
                    y=base_y + padding_y,
                    width=row_width * cell_width - 2 * padding_x,
                    height=col_width * cell_height - 2 * padding_y,
                    rx=CELL_RADIUS,
                    ry=CELL_RADIUS,
                    fill=colours["greyer"],
                ),
                svg.Text(
                    text=day,
                    x=base_x + (row_width * cell_width) / 2,
                    y=base_y + DAY_TEXT_HEIGHT - (cell_height / 20 if num_rows == 3 else 0),  # noqa: PLR2004
                    font_size=DAY_TEXT_SIZE,
                    text_anchor="middle",
                    class_=["title"],
                ),
            ]
        )

        for col in range(col_width):
            for row in range(row_width):
                event_scale = 0.85 if num_rows == 3 else 1.1  # noqa: PLR2004

                # work out extra translation required
                translate_x = base_x + row * cell_width + cell_width / 2
                translate_y = base_y + col * cell_height + cell_height / 2 + DAY_TEXT_HEIGHT / 2

                # events are slightly too low
                if num_rows == 3:  # noqa: PLR2004
                    translate_y -= cell_height / 20
                else:
                    translate_y -= cell_height / 30

                # if spanning multiple columns, pull towards centre
                pull_y = 0 if col_width == 1 else pull_factor
                translate_y = (1 - pull_y) * translate_y + pull_y * centre_y

                translate_x /= event_scale
                translate_y /= event_scale

                # create event circle and apply offset + scaling around its center
                event_idx = col * row_width + row
                event_circle = get_event_circle(day_event_list[event_idx], True, False)
                event_circle.transform = [
                    svg.Scale(event_scale),
                    svg.Translate(translate_x, translate_y),
                ]
                elements.append(event_circle)

    return elements
