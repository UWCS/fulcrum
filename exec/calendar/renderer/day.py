import svg

from exec.calendar.config import MAX_EVENTS_IN_CIRCLE
from exec.calendar.renderer.event import get_event_circle


def create_day_circle(events: list[dict], day_size: float, for_figma: bool) -> svg.G:
    """create a circle for a day in multi week view"""
    # add the base background circle
    elements: list[svg.Element] = [svg.Circle(cx=0, cy=0, r=(day_size * 0.95) / 2, fill="#363A3E")]

    # truncate events to max allowed
    events = events[:MAX_EVENTS_IN_CIRCLE]

    # create offset tuples to position events (x, y, scale)
    offset = day_size / 3
    extra_offset = offset + day_size / 24
    scales = [1.0, 0.65, 0.55, 0.55]
    offsets = [
        [],
        [(0, 0, scales[0])],
        [(-offset, -offset, scales[1]), (offset, offset, scales[1])],
        [
            (-extra_offset, -extra_offset, scales[2]),
            (extra_offset, -extra_offset, scales[2]),
            (0, extra_offset, scales[2]),
        ],
        [
            (-extra_offset, -extra_offset, scales[3]),
            (extra_offset, -extra_offset, scales[3]),
            (-extra_offset, extra_offset, scales[3]),
            (extra_offset, extra_offset, scales[3]),
        ],
    ]

    # add the event circles
    event_circles = []
    for (x, y, scale), event in zip(offsets[len(events)], events, strict=True):
        event_circle = get_event_circle(event, False, for_figma)
        event_circle.transform = [
            svg.Scale(0.6 * scale),  # overall scale to fit in day circle
            svg.Translate(x / scale, y / scale),
        ]
        event_circles.append(event_circle)
    elements.extend(reversed(event_circles))  # reverse to have first event on top

    return svg.G(elements=elements)
