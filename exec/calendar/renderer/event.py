import svg

from config import colours, icon_paths
from exec.calendar.config import CIRCLE_SIZE
from exec.calendar.svg_utils import convert_path_to_list


def split_text(text: str, max_chars: int) -> list[str]:
    """split a title into multiple lines if too long"""
    if len(text) <= max_chars:
        return [text]

    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def get_event_circle(event: dict, display_location: bool, for_figma: bool) -> svg.G:
    """Create a circle for an event"""
    icon = event.get("icon", "")
    if icon is not None:
        icon = icon.lower().removeprefix("ph-")
    title = split_text(event["name"], 12)
    location = split_text(event["location"], 15) if display_location else []
    colour = event.get("colour", colours["blue"])
    if not colour.startswith("#"):
        colour = colours.get(colour, colours["blue"])
    start_time = event["start_time"]
    time_format = "%I%p" if start_time.minute == 0 else "%I:%M%p"
    time_str = start_time.strftime(time_format).lstrip("0")

    # sizing params
    radius = CIRCLE_SIZE / 2
    text_top = CIRCLE_SIZE / 8 if icon else -CIRCLE_SIZE / 20

    # font sized based on if location is displayed
    if display_location:
        title_size = CIRCLE_SIZE / 8 if len(title) == 1 else CIRCLE_SIZE / 10
        location_size = CIRCLE_SIZE / 13 if len(location) == 1 else CIRCLE_SIZE / 16
        time_size = location_size
    else:
        # grow title and time if no location
        title_size = CIRCLE_SIZE / 7 if len(title) == 1 else CIRCLE_SIZE / 9
        location_size = 0  # not used
        time_size = CIRCLE_SIZE / 9

    # combine into list
    font_sizes = (
        [title_size] * len(title)
        + ([location_size] * len(location) if display_location else [])
        + [time_size]
    )

    elements: list[svg.Element] = [svg.Circle(cx=0, cy=0, r=radius, fill=colour)]

    if icon and icon in icon_paths:
        path, width, height, min_x, min_y = convert_path_to_list(icon_paths[icon])

        # scale the icon to be 150x150 max
        desired_size = CIRCLE_SIZE / 2.666
        scale = desired_size / max(width, height)

        # centre the icon vertically in the space above the text
        target_y = (-radius + text_top) / 2

        elements.append(
            svg.Path(
                d=path,
                fill="white",
                transform=[
                    svg.Translate(0, target_y),  # move to centre position
                    svg.Scale(scale),  # scale to desired size
                    svg.Translate(-min_x - width / 2, -min_y - height / 2),  # centre
                ],
            )
        )

    lines = title + location + [time_str]
    current_y = text_top
    for i, (line, size) in enumerate(zip(lines, font_sizes, strict=True)):
        elements.append(
            svg.Text(
                text=line,
                x=0,
                y=current_y,
                font_size=size,
                text_anchor="middle",
                class_=["title" if i < len(title) or for_figma else "text"],
            )
        )
        current_y += size

    return svg.G(elements=elements)
