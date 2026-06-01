"""API Blueprint views.

Health endpoint plus one view per ported route, preserving method, path,
status code, and JSON shape. Attached to api_bp from app.api.
"""
from app.api import api_bp


@api_bp.get("/health")
def health():
    return {"status": "ok"}, 200
