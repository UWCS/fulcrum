from flask import Blueprint, Response, jsonify, request

from schema import Event, Tag
from search.utils import get_results, get_suggestions

search_api_bp = Blueprint("search_api", __name__, url_prefix="/api/search")


@search_api_bp.route("/suggestions/", methods=["GET"])
def search_suggestions() -> tuple[Response, int]:
    """Get search completion suggestions
    ---
    security: []
    parameters:
      - name: query
        in: query
        type: string
        required: true
        description: The search query to get suggestions for
      - name: limit
        in: query
        type: integer
        required: false
        default: 5
        description: The maximum number of suggestions to return (-1 for no limit)
    responses:
        200:
            description: a list of search suggestions (empty if no suggestions)
            schema:
                type: array
                items:
                    type: string
                    example: "completion suggestion 1"
    """

    query = request.args.get("query", "").lower()
    limit = request.args.get("limit", 5, type=int)

    if not query:
        return jsonify([]), 200

    return jsonify(get_suggestions(query, limit)), 200


@search_api_bp.route("/", methods=["GET"])
def search() -> tuple[Response, int]:
    """Search results for site, can return events, tags, categories
    ---
    security: []
    parameters:
      - name: query
        in: query
        type: string
        required: true
        description: The search query to get results for
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
        description: The maximum number of results to return (use -1 for no limit)
    responses:
      200:
        description: a list of search results
        schema:
          type: array
          items:
            type: object
            properties:
              type:
                type: string
                enum: [event, tag, category]
                description: The type of result
              data:
                oneOf:
                  - $ref: '#/definitions/Event'
                  - $ref: '#/definitions/Tag'
                  - type: string
                description: The actual result data
            required:
              - type
              - data
          example:
            - type: event
              data:
                id: 1
                name: "Sample Event"
            - type: tag
              data:
                id: 1
                label: "Sample Tag"
            - type: category
              data: "Sample Category"
    """

    query = request.args.get("query", "").lower()
    limit = request.args.get("limit", 10, type=int)

    if not query:
        return jsonify([]), 200

    results = get_results(query, limit)

    json = []
    for result in results:
        if isinstance(result, str):
            json.append({"type": "category", "data": result})
        elif isinstance(result, Tag):
            json.append({"type": "tag", "data": result.to_dict()})
        elif isinstance(result, Event):
            json.append({"type": "event", "data": result.to_dict()})

    return jsonify(json), 200
