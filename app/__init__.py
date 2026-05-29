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
from flask.logging import default_handler

from app.config import get_config
from app.extensions import register_extensions
from app.errors import register_error_handlers
from app.middleware import register_middleware
from app.api import api_bp


# Single source of truth for the contracted request-log line format (AAP §0.5.2).
# Records emitted through ``app.logger`` (e.g. the request entry/exit lines in
# app/middleware.py) are rendered as::
#
#     "2026-05-29 17:56:52,558 INFO app: --> GET /health [<request-id>]"
#
# This deliberately differs from Flask's built-in default
# ("[%(asctime)s] %(levelname)s in %(module)s: %(message)s") so downstream log
# aggregation can rely on a non-bracketed timestamp and the logger ``name``
# token (here, "app"). Keeping it as a module-level constant makes the contract
# the single point of change and lets tests assert against it directly.
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

# Marker attribute set on the handler this module installs. ``app.logger`` is a
# process-wide, name-shared logger ("app"); the application factory may run
# multiple times in one process (notably the function-scoped ``app`` test
# fixture calls ``create_app`` once per test). The marker lets
# :func:`configure_logging` recognize its own handler and stay idempotent so
# repeated calls never accumulate duplicate handlers (and therefore duplicate
# log lines).
_REQUEST_LOG_HANDLER_FLAG = "_artifact4_request_log_handler"


def configure_logging(app):
    """Apply the contracted log format and level to ``app.logger``.

    The log level is resolved from the application's ``LOG_LEVEL`` config value
    (defaulting to ``"INFO"``). Unknown level names fall back to ``INFO`` via
    :func:`getattr`, so an invalid configuration never raises. The level is
    (re)applied unconditionally on every call so ``LOG_LEVEL`` is always honored.

    Flask attaches its module-level :data:`flask.logging.default_handler` to
    ``app.logger`` lazily, the first time the ``app.logger`` attribute is read.
    Because that handler carries Flask's *default* format
    (``"[%(asctime)s] %(levelname)s in %(module)s: %(message)s"``), any naive
    ``if not app.logger.handlers:`` guard sees a non-empty handler list (the act
    of evaluating the guard triggers the lazy attach) and never installs a
    custom handler — leaving the contracted format unapplied. To guarantee the
    contracted :data:`LOG_FORMAT` actually takes effect, this function first
    removes Flask's default handler, then installs its own
    :class:`logging.StreamHandler`.

    The function is idempotent: the installed handler is tagged with
    :data:`_REQUEST_LOG_HANDLER_FLAG`, and a new handler is added only when no
    tagged handler is already present. This matters because ``app.logger`` is a
    process-wide, name-shared logger, so repeated invocations (e.g. the
    function-scoped ``app`` test fixture calling :func:`create_app` per test) do
    not accumulate duplicate handlers or duplicate log lines.
    ``Logger.removeHandler`` is a safe no-op when the handler is absent.

    Args:
        app: The :class:`flask.Flask` application whose logger is configured.
    """
    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    # Drop Flask's lazily-attached default handler so its bracketed default
    # format does not shadow the contracted LOG_FORMAT below. Safe no-op when
    # the default handler was never attached (e.g. on a repeated call).
    app.logger.removeHandler(default_handler)
    # Install our contracted-format handler exactly once (idempotent across
    # repeated create_app() calls in the same process).
    if not any(getattr(h, _REQUEST_LOG_HANDLER_FLAG, False) for h in app.logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        setattr(handler, _REQUEST_LOG_HANDLER_FLAG, True)
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
                             then mirror JSON_SORT_KEYS onto app.json.sort_keys
                             (Flask 3 JSON-provider API; the config key alone is
                             inert in Flask 3.x)
        2. logging         -> configure_logging(app)
        3. extensions      -> register_extensions(app)
        4. blueprint       -> app.register_blueprint(api_bp)  (no url_prefix)
        5. error handlers  -> register_error_handlers(app)
        6. request hooks   -> register_middleware(app)

    The blueprint is registered with **no** ``url_prefix`` so that ``/health``
    and every ported route live at the application root.

    Flask's built-in static route is **disabled** (``static_folder=None``) so
    the baseline runtime route map exposes only the registered blueprint views
    (e.g. ``/health``) and never ``/static/<path:filename>``. Serving static
    assets is out of scope for the baseline and is only added once the original
    Node.js source proves it is part of the contract (AAP §0.6.2; rule R3, "no
    invented endpoints").

    Args:
        config: Selects the configuration to load. May be a config name
            string (e.g. ``"testing"``), a config class/object, or ``None``.
            All resolution is delegated to :func:`app.config.get_config`;
            unknown names fall back gracefully to the development config.

    Returns:
        flask.Flask: The configured application instance, ready to serve.
    """
    # Disable Flask's default static route (``static_folder=None``). The
    # baseline scaffold must expose ONLY the routes it explicitly registers; the
    # default ``/static/<path:filename>`` route is an invented endpoint relative
    # to the (absent) original Node.js server and is therefore out of scope
    # (AAP §0.6.2; rule R3). Static-file serving is reintroduced only if the
    # original source proves it is part of the contract.
    app = Flask(__name__, static_folder=None)
    app.config.from_object(get_config(config))
    # Flask 3 removed the ``JSON_SORT_KEYS`` *config* key; key-sorting behavior
    # now lives on the JSON provider (``app.json``). Mirror the loaded config
    # value onto the provider so the intended unsorted-key output (response
    # byte-parity with the original server) is actually applied. Falls back to
    # ``False`` if a config object omits the key.
    app.json.sort_keys = app.config.get("JSON_SORT_KEYS", False)
    configure_logging(app)
    register_extensions(app)
    app.register_blueprint(api_bp)
    register_error_handlers(app)
    register_middleware(app)
    return app
