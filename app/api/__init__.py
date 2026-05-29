"""API Blueprint package initializer.

Defines api_bp and imports the route module so views register at import time.
Registered in the factory with NO url_prefix so routes live at the app root.
"""
from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.api import routes  # noqa: E402,F401  (import after api_bp is defined)
