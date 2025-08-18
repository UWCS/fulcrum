from flask import Blueprint, Response, jsonify, request

search_api_bp = Blueprint("search_api", __name__, url_prefix="/api/search")


@search_api_bp.route("/complete/", methods=["GET"])
def search_complete() -> tuple[Response, int]:
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
        description: The maximum number of suggestions to return
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

    if not query or limit <= 0:
        return jsonify([]), 200

    return jsonify(["Apple", "Banana", "Cherry", "Date"][:limit]), 200


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
        description: The maximum number of results to return
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

    return jsonify([]), 200
