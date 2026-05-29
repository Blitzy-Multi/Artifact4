"""Centralized JSON error handlers (Express error-middleware parity).

Returns consistent JSON error bodies with matching HTTP status codes.
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


def _error_response(status, error, message):
    response = jsonify({"error": error, "message": message})
    response.status_code = status
    return response


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(err):
        return _error_response(400, "Bad Request", getattr(err, "description", "Bad request"))

    @app.errorhandler(404)
    def not_found(err):
        return _error_response(404, "Not Found", getattr(err, "description", "Resource not found"))

    @app.errorhandler(405)
    def method_not_allowed(err):
        return _error_response(405, "Method Not Allowed", getattr(err, "description", "Method not allowed"))

    @app.errorhandler(500)
    def internal_error(err):
        return _error_response(500, "Internal Server Error", "An unexpected error occurred")

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return _error_response(err.code or 500, err.name, err.description)
