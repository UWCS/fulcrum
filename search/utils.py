from typing import Iterator

from sqlalchemy import func

from config import categories
from schema import Event, Tag, db


def _search_pipeline(query: str) -> Iterator[tuple[str, Event | Tag | str]]:
    """Generator that yields search results from the database"""
    query = query.strip().lower()
    if not query:
        return []

    # categories first as most generic
    for category in categories:
        if query in category:
            yield "category", category

    # tags as can be more specific
    # use ilike for generic matching
    tags = Tag.query.filter(Tag.name.ilike(f"%{query}%")).all()  # type: ignore
    for tag in tags:
        yield "tag", tag

    # events is most specific
    # prefer title over location as more relevant
    events = (
        db.session.query(Event)
        .filter(Event.name.ilike(f"%{query}%"), Event.draft.is_(False))  # type: ignore
        .order_by(func.abs(Event.start_time - func.now()))  # prefer events closer to now
        .all()
    )
    for event in events:
        yield "title", event

    events = (
        db.session.query(Event)
        .filter(Event.location.ilike(f"%{query}%"), Event.draft.is_(False))  # type: ignore
        .order_by(func.abs(Event.start_time - func.now()))
        .all()
    )
    for event in events:
        yield "location", event


def get_suggestions(query: str, limit: int = 5) -> list[str]:
    """
    Get search suggestions based on the query
    Order: categories -> tags -> event title -> event location
    """
    seen = set()
    results = []

    for kind, result in _search_pipeline(query):
        if kind == "category":
            value = result
        elif isinstance(result, Tag):
            value = result.name
        elif isinstance(result, Event):
            value = result.name if kind == "title" else result.location
        else:
            continue

        if value not in seen:
            seen.add(value)
            results.append(value)

        if len(results) >= limit > 0:
            break

    return results


def get_results(query: str, limit: int = 10) -> list[Event | Tag | str]:
    """
    Get search results based on the query
    Order: categories -> tags -> event title -> event location
    """
    seen = set()
    results = []

    for _, result in _search_pipeline(query):
        key = result if isinstance(result, (Event, Tag)) else result.lower()
        if key not in seen:
            seen.add(key)
            results.append(result)

        if len(results) >= limit > 0:
            break

    return results
