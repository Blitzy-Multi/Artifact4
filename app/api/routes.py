"""API Blueprint views.

Health endpoint plus one view per ported route, preserving method, path,
status code, and JSON shape. Attached to api_bp from app.api.
"""
from flask import Response

from app.api import api_bp


@api_bp.get("/health")
def health():
    return {"status": "ok"}, 200


@api_bp.get("/good-evening")
def good_evening():
    # User-requested greeting endpoint, added alongside the existing
    # /health route. Returns the literal greeting as plain text (HTTP 200).
    return Response("Good evening", mimetype="text/plain")
