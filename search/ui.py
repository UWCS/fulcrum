from flask import Blueprint, render_template, request

from schema import Event, Tag
from search.utils import get_results

search_ui_bp = Blueprint("search_ui", __name__, url_prefix="/search")


@search_ui_bp.route("/", methods=["GET"])
def search() -> str:
    """View search results"""
    # TODO: maybe add pagination or infinite scroll (https://getbootstrap.com/docs/5.3/components/pagination/)

    original_query = request.args.get("query", "")
    query = original_query.strip().lower()
    limit = request.args.get("limit", -1, type=int)

    if not query:
        return render_template("search.html", results=[])

    results = get_results(query, limit)
    categories, tags, events = [], [], []
    for result in results:
        if isinstance(result, str):
            categories.append(result)
        elif isinstance(result, Tag):
            tags.append(result)
        elif isinstance(result, Event):
            events.append(result)

    return render_template(
        "search.html",
        categories=categories,
        tags=tags,
        events=events,
        original_query=original_query,
    )
