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
