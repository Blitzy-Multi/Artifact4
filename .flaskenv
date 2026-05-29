# .flaskenv - environment configuration for the Flask command-line interface.
#
# Read automatically by the `flask` CLI on startup (via python-dotenv), so commands
# such as `flask run` work without manually exporting variables. This file holds
# NON-SECRET configuration only and IS committed to the repository. Real secrets
# (e.g. SECRET_KEY) belong in ".env", which is git-ignored; never place them here.

# Import path to the WSGI entrypoint module that exposes the `app` object, so the
# Flask CLI can locate and load the application (mirrors `gunicorn wsgi:app`).
FLASK_APP=wsgi.py

# Target environment for local development runs. Note: Flask 2.3+/3.x no longer
# derives debug mode from FLASK_ENV (FLASK_DEBUG does); it is retained here to
# explicitly signal the development environment for tooling and any code that
# inspects it. The active configuration class is selected via APP_CONFIG in
# ".env" (see .env.example).
FLASK_ENV=development

# Enable the interactive debugger and the auto-reloader during development
# (the Python equivalent of Node's nodemon). Set to 0 for production.
FLASK_DEBUG=1
