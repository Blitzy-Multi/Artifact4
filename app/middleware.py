"""Request/response hooks reproducing Express app.use() middleware ordering.

Installs before_request / after_request hooks for request logging, correlation
IDs, and standard response headers.
"""
import time
import uuid

from flask import g, request


def register_middleware(app):
    @app.before_request
    def _assign_correlation_id():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        g.start_time = time.time()
        app.logger.info("--> %s %s [%s]", request.method, request.path, g.request_id)

    @app.after_request
    def _log_and_tag_response(response):
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id
        start = getattr(g, "start_time", None)
        if start is not None:
            duration_ms = (time.time() - start) * 1000.0
            response.headers["X-Response-Time"] = "%.2fms" % duration_ms
            app.logger.info(
                "<-- %s %s %s (%.2fms) [%s]",
                request.method, request.path, response.status_code, duration_ms, request_id,
            )
        return response
