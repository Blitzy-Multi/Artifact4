"""Centralized JSON error handlers (Express error-middleware parity).

Returns consistent JSON error bodies with matching HTTP status codes while
preserving the protocol headers that Werkzeug attaches to the original
``HTTPException`` (most importantly the ``Allow`` header on ``405 Method Not
Allowed`` responses, but also e.g. ``Retry-After`` on ``429`` and
``WWW-Authenticate`` on ``401``). Rebuilding the body with :func:`flask.jsonify`
would otherwise drop those headers and break the HTTP contract.
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException

# Headers that describe the JSON body itself. They are owned by the freshly
# built ``jsonify`` response and must never be copied over from the original
# Werkzeug (text/html) error response, otherwise the advertised content type or
# length would not match the JSON payload we return.
_BODY_OWNED_HEADERS = frozenset({"content-type", "content-length"})


def _error_response(status, error, message, original=None):
    """Build the canonical JSON error envelope ``{"error", "message"}``.

    Args:
        status: HTTP status code to set on the response.
        error: Short error name (e.g. ``"Method Not Allowed"``).
        message: Human-readable detail string.
        original: Optional source :class:`~werkzeug.exceptions.HTTPException`.
            When provided, its protocol headers (everything except the
            body-owned ``Content-Type``/``Content-Length``) are copied onto the
            JSON response so headers such as ``Allow`` are not lost.

    Returns:
        flask.Response: A JSON response carrying the error envelope, the given
        status code, and any preserved protocol headers from ``original``.
    """
    response = jsonify({"error": error, "message": message})
    response.status_code = status

    # Preserve protocol headers from the original Werkzeug exception response so
    # the JSON envelope remains a faithful, spec-compliant HTTP response. The
    # canonical case is ``Allow`` on a 405: Flask/Werkzeug know the permitted
    # method set (proven by the OPTIONS response) and surface it via the
    # exception's response headers; rebuilding the body here would otherwise
    # discard it.
    if original is not None:
        try:
            original_headers = original.get_response().headers
        except Exception:  # pragma: no cover - defensive; get_response is stable
            original_headers = None
        if original_headers is not None:
            for key, value in original_headers.items():
                if key.lower() in _BODY_OWNED_HEADERS:
                    continue
                response.headers[key] = value
    return response


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(err):
        return _error_response(
            400, "Bad Request", getattr(err, "description", "Bad request"), original=err
        )

    @app.errorhandler(404)
    def not_found(err):
        return _error_response(
            404, "Not Found", getattr(err, "description", "Resource not found"), original=err
        )

    @app.errorhandler(405)
    def method_not_allowed(err):
        # Preserve the ``Allow`` header that Werkzeug's ``MethodNotAllowed``
        # response carries so clients still learn which methods are supported.
        return _error_response(
            405,
            "Method Not Allowed",
            getattr(err, "description", "Method not allowed"),
            original=err,
        )

    @app.errorhandler(500)
    def internal_error(err):
        # ``err`` here may be a non-HTTP exception (e.g. an uncaught error), so
        # it is intentionally NOT forwarded as ``original``: a generic
        # exception has no ``get_response`` and no protocol headers to preserve,
        # and the response must stay generic to avoid leaking internals.
        return _error_response(500, "Internal Server Error", "An unexpected error occurred")

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return _error_response(err.code or 500, err.name, err.description, original=err)
