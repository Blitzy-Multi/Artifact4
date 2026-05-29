"""Application factory for the Flask server.

This module is the single integration point that assembles the entire
application. It exposes :func:`create_app`, an application-factory callable
that builds and wires a fully configured :class:`flask.Flask` instance, and
:func:`configure_logging`, a helper that attaches a stream log handler to the
application logger.

The factory mirrors the initialization ordering of the original Express
server for behavioral parity (AAP §0.5.2). The fixed registration order is::

    config -> logging -> extensions -> blueprint -> error handlers -> request hooks

Typical usage::

    # wsgi.py
    from app import create_app
    app = create_app(os.getenv("APP_CONFIG"))

    # tests/conftest.py
    app = create_app("testing")

Only the Flask framework, Werkzeug, python-dotenv and the Python standard
library are imported at the baseline; conditional capabilities (CORS, ORM,
JWT, outbound HTTP, etc.) are intentionally absent because the original
Node.js source is not present in the repository (AAP §0.5.1, §0.6.2).
"""
import logging

from flask import Flask

from app.config import get_config
from app.extensions import register_extensions
from app.errors import register_error_handlers
from app.middleware import register_middleware
from app.api import api_bp


def configure_logging(app):
    """Attach a stream log handler to ``app.logger`` and set its level.

    The log level is resolved from the application's ``LOG_LEVEL`` config value
    (defaulting to ``"INFO"``). Unknown level names fall back to ``INFO`` via
    :func:`getattr`, so an invalid configuration never raises.

    The function is idempotent: a :class:`logging.StreamHandler` is only added
    when ``app.logger`` has no handlers, so repeated invocations (or repeated
    calls to :func:`create_app` within the same process) do not accumulate
    duplicate handlers. The level is (re)applied on every call.

    Args:
        app: The :class:`flask.Flask` application whose logger is configured.
    """
    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        app.logger.addHandler(handler)
    app.logger.setLevel(level)


def create_app(config=None):
    """Build and return a fully configured Flask application.

    This is the application-factory entry point. It instantiates the Flask
    app, loads configuration, and wires logging, extensions, the API blueprint,
    error handlers, and request hooks in a fixed order that mirrors the
    original Express middleware initialization for behavioral parity.

    Registration order (do not reorder)::

        1. config         -> app.config.from_object(get_config(config))
        2. logging         -> configure_logging(app)
        3. extensions      -> register_extensions(app)
        4. blueprint       -> app.register_blueprint(api_bp)  (no url_prefix)
        5. error handlers  -> register_error_handlers(app)
        6. request hooks   -> register_middleware(app)

    The blueprint is registered with **no** ``url_prefix`` so that ``/health``
    and every ported route live at the application root.

    Args:
        config: Selects the configuration to load. May be a config name
            string (e.g. ``"testing"``), a config class/object, or ``None``.
            All resolution is delegated to :func:`app.config.get_config`;
            unknown names fall back gracefully to the development config.

    Returns:
        flask.Flask: The configured application instance, ready to serve.
    """
    app = Flask(__name__)
    app.config.from_object(get_config(config))
    configure_logging(app)
    register_extensions(app)
    app.register_blueprint(api_bp)
    register_error_handlers(app)
    register_middleware(app)
    return app
