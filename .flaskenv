FLASK_APP=wsgi.py
FLASK_DEBUG=1
# Development opts IN to the development configuration. The Flask CLI loads this
# file for `flask run`, so the dev server selects DevelopmentConfig. gunicorn
# does NOT read .flaskenv, so `gunicorn wsgi:app` defaults to production (debug
# off) via wsgi.py -- keeping the bare production command safe.
APP_CONFIG=development
