"""WSGI entrypoint for the Artifact4 Flask application.

This module is the single, well-known location from which both the production
WSGI server and the Flask CLI load the application. It builds the application
via the :func:`app.create_app` application-factory and binds the result to a
module-level callable named ``app`` so that the import string ``wsgi:app``
resolves everywhere it is referenced:

* Production:  ``gunicorn wsgi:app``      (see ``Procfile``)
* Development: ``flask run``              (see ``.flaskenv`` -> ``FLASK_APP=wsgi.py``)
* Direct:      ``python wsgi.py``         (uses the ``__main__`` block below)

Design notes
------------
* This file is intentionally *thin*. It contains no routes, configuration, or
  business logic; all of that lives inside the ``app`` package and is assembled
  by :func:`app.create_app`. Keeping the entrypoint minimal is the idiomatic
  Flask application-factory pattern and keeps the ``wsgi:app`` contract stable.
* Configuration selection is environment-driven and **fails safe to
  production**. The ``APP_CONFIG`` environment variable
  (``development`` | ``production`` | ``testing``) is read here and handed to
  the factory; when it is unset this entrypoint defaults it to ``production``
  so the bare production command ``gunicorn wsgi:app`` is safe (debug off) with
  no extra environment plumbing. The development server opts IN to development:
  ``.flaskenv`` sets ``APP_CONFIG=development`` and is loaded by the Flask CLI
  for ``flask run`` (gunicorn does NOT read ``.flaskenv``), so ``flask run``
  selects development while ``gunicorn wsgi:app`` stays production by default.
* Environment variables are loaded from a local ``.env`` file (via
  ``python-dotenv``) *before* the ``app`` package is imported. This is required
  because configuration is read from ``os.environ`` at import time, so loading
  ``.env`` afterwards would be too late for ``gunicorn wsgi:app`` and direct
  WSGI imports. The call is idempotent and never overrides already-exported
  values, so the ``flask run`` path (which loads ``.env`` itself) is unaffected.

Environment variables
---------------------
APP_CONFIG
    Selects the configuration profile passed to :func:`app.create_app`.
    Optional; this entrypoint defaults it to ``production`` when it is absent so
    the bare ``gunicorn wsgi:app`` command is production-safe. ``flask run``
    selects ``development`` explicitly via ``.flaskenv``.
PORT
    TCP port used only by the ``__main__`` development runner below. Defaults
    to ``5000``. Production servers (gunicorn) bind the port themselves (see
    ``Procfile``) and never execute the ``__main__`` block.
"""
import os

from dotenv import load_dotenv

# Load environment variables from a local ``.env`` file BEFORE importing the
# application package. ``app.config`` (see ``app/config.py``) reads
# ``os.environ`` at import/class-definition time, so the ``.env`` values must be
# present in the environment first; otherwise ``gunicorn wsgi:app`` and direct
# WSGI imports would silently ignore ``.env`` and fall back to development
# defaults (e.g. ``dev-secret-change-me``). The Flask CLI already loads ``.env``
# for ``flask run`` before importing this module, so this call is idempotent
# there: by default ``load_dotenv`` does NOT override variables already set in
# the environment, leaving the ``flask run`` path unaffected.
load_dotenv()

from app import create_app  # noqa: E402  (intentionally imported after load_dotenv)

# Module-level WSGI application callable.
#
# ``wsgi:app`` is the import string used by gunicorn (``Procfile``) and the
# Flask CLI (``.flaskenv`` -> ``FLASK_APP=wsgi.py``). Configuration selection
# fails safe to PRODUCTION: when ``APP_CONFIG`` is unset, the bare
# ``gunicorn wsgi:app`` command must run with production posture (debug off)
# without requiring an unstated environment variable. Development is opt-in via
# ``.flaskenv`` (``APP_CONFIG=development``), which the Flask CLI loads for
# ``flask run`` but gunicorn does not, so ``flask run`` selects development
# while ``gunicorn wsgi:app`` defaults to production.
app = create_app(os.getenv("APP_CONFIG", "production"))


if __name__ == "__main__":
    # Direct execution (``python wsgi.py``) starts Flask's built-in WSGI server
    # using the ``app`` built above. Because this path does NOT load
    # ``.flaskenv``, it inherits the same production-safe default as gunicorn
    # (``APP_CONFIG`` -> ``production`` when unset); export ``APP_CONFIG`` (or
    # use the development workflow ``flask run``, which loads ``.flaskenv``) to
    # select another profile. Production deployments use gunicorn (see
    # ``Procfile``), which imports ``app`` above and never runs this block.
    # Binding ``0.0.0.0`` exposes the server on all interfaces so it is
    # reachable from outside a container; the port is read from ``PORT`` and
    # defaults to ``5000`` to mirror the documented configuration.
    #
    # ``load_dotenv=False`` is REQUIRED to keep the "does NOT load ``.flaskenv``"
    # guarantee above actually true. By default ``Flask.run()`` re-runs the Flask
    # CLI's dotenv loader (``flask.cli.load_dotenv()``), which loads BOTH ``.env``
    # AND ``.flaskenv``; it then honors ``FLASK_DEBUG`` from that file
    # (``if "FLASK_DEBUG" in os.environ: self.debug = get_debug_flag()``). Since
    # ``.flaskenv`` ships ``FLASK_DEBUG=1`` for the ``flask run`` dev workflow,
    # leaving this at the default would silently flip the interactive debugger ON
    # here and override the production posture selected above -- contradicting the
    # fail-safe-to-production contract (AAP rule R6) and exposing the Werkzeug
    # debugger (remote code execution) on a "production-safe" command. Disabling
    # it pins ``app.debug`` to the value from the selected config class. The
    # module-level ``load_dotenv()`` call above still loads ``.env`` (only), so
    # ``.env``-based configuration continues to work for this path.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), load_dotenv=False)
