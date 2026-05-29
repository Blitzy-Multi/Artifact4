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
* Configuration selection is environment-driven. The ``APP_CONFIG`` environment
  variable (``development`` | ``production`` | ``testing``) is read and handed
  to the factory; when it is unset the factory falls back to its own default
  (``development``), so a missing value is always safe.

Environment variables
---------------------
APP_CONFIG
    Selects the configuration profile passed to :func:`app.create_app`.
    Optional; the factory defaults to ``development`` when it is absent.
PORT
    TCP port used only by the ``__main__`` development runner below. Defaults
    to ``5000``. Production servers (gunicorn) bind the port themselves (see
    ``Procfile``) and never execute the ``__main__`` block.
"""
import os

from app import create_app

# Module-level WSGI application callable.
#
# ``wsgi:app`` is the import string used by gunicorn (``Procfile``) and the
# Flask CLI (``.flaskenv`` -> ``FLASK_APP=wsgi.py``). The factory resolves
# ``APP_CONFIG`` to a concrete configuration object; passing ``None`` (when the
# variable is unset) is explicitly supported by the factory and yields the
# default development configuration.
app = create_app(os.getenv("APP_CONFIG"))


if __name__ == "__main__":
    # Direct execution (``python wsgi.py``) starts Flask's built-in development
    # server. This path is for local development only -- production deployments
    # use gunicorn (see ``Procfile``), which imports ``app`` above and never
    # runs this block. Binding ``0.0.0.0`` exposes the server on all interfaces
    # so it is reachable from outside a container; the port is read from
    # ``PORT`` and defaults to ``5000`` to mirror the documented configuration.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
