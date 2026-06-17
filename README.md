# Artifact4

Artifact4 is a **Python 3 / [Flask](https://flask.palletsprojects.com/)** reimplementation of an
existing **Node.js** HTTP server. It is a faithful, backward‑compatible **port** — not a redesign or
an enhancement — built for full **behavioral parity** with the original: every route (HTTP method +
path), request/response JSON shape, HTTP status code, response header, authentication/session
behavior, input validation, error‑response format, logging, and side effect is reproduced so that
existing clients cannot distinguish this server from the original at the API boundary.

The application is built to idiomatic Flask conventions: the **application-factory pattern**
(`create_app()`), **Blueprints** for route grouping, a dedicated configuration module, centralized
JSON error handlers, request hooks for middleware parity, and a WSGI entrypoint for production. The
server is **fully assembled and runnable**: the application factory (`app/__init__.py`), the
environment-driven configuration module (`app/config.py`), the API Blueprint (`app/api/`) exposing
`GET /health`, the centralized JSON error handlers (`app/errors.py`), the request hooks
(`app/middleware.py`), the extension-wiring seam (`app/extensions.py`), and the WSGI entrypoint
(`wsgi.py`) are all present and wired together. The baseline parity **test suite** (`tests/`) is also
present and passing (see [Testing](#testing) and the source-of-truth note below).

> **Source-of-truth note**
>
> Functional parity is defined relative to the original Node.js implementation, which is **not yet
> present in this repository**. The port is delivered in milestones. **This checkpoint delivers a
> runnable Flask application**: the application factory (`app/__init__.py`), the configuration module
> (`app/config.py`), the API Blueprint (`app/api/`) with the `GET /health` endpoint, the WSGI
> entrypoint (`wsgi.py`), the request/response middleware (`app/middleware.py`), the centralized JSON
> error handlers (`app/errors.py`), and the extension-wiring seam (`app/extensions.py`) are all
> present and wired together, alongside the dependency manifests, environment templates, and tooling.
> **The baseline parity test suite — `tests/conftest.py`, `tests/test_health.py`, and
> `tests/test_api.py` — is present and passing**, covering the `GET /health` endpoint plus the
> baseline error-handling and middleware behavior. The exact application-specific endpoints, models,
> services, validation schemas, and authentication are then ported **one-to-one** from the original
> routes once that source is provided; a single placeholder parity test is intentionally skipped until
> then. No business endpoints are invented here.

## Prerequisites

- **Python 3.12.x** (recommended). Flask 3.1.x officially supports **Python 3.9+**, so any 3.9 or
  newer interpreter works; 3.12.x is the recommended target runtime.
- **pip** — the Python package installer (bundled with modern Python releases).
- **venv** — the standard‑library virtual‑environment tool (used to isolate dependencies).

## Setup

All commands are run from the repository root.

1. **Create and activate a virtual environment.**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows (PowerShell or Command Prompt):

   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Install runtime dependencies.**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install development / test dependencies** (this also pulls in the runtime dependencies via
   `-r requirements.txt`, provisioning a single environment that can both run and test the app):

   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Create your local environment file** from the template, then edit the values:

   ```bash
   cp .env.example .env
   ```

   The `.env` file is git‑ignored and is loaded automatically at startup by `python-dotenv`: the
   WSGI entrypoint (`wsgi.py`) calls `load_dotenv()` before the application is imported, so
   `gunicorn wsgi:app`, `python wsgi.py`, and `flask run` all pick up your `.env` values. Never
   commit real secrets — populate `.env` locally (see [Configuration](#configuration)).

## Running the Server

The server is **runnable now**. The WSGI entrypoint (`wsgi.py`) exposes `app = create_app(...)`, and
the application factory wires configuration, logging, the API Blueprint, error handlers, and request
hooks. Use the development or production workflow below.

### Development

The Flask CLI reads `.flaskenv`, which sets `FLASK_APP=wsgi.py`, so no manual exports are required:

```bash
flask run
```

By default the development server listens on **http://127.0.0.1:5000**. To enable the interactive
debugger and the auto‑reloader (the Python equivalent of Node's `nodemon`):

```bash
flask run --debug
```

To serve on a different host/port, pass the CLI flags explicitly:

```bash
flask run --host 0.0.0.0 --port 5000
```

### Production

Use the [Gunicorn](https://gunicorn.org/) WSGI server (this replaces `node server.js` / `pm2`):

```bash
gunicorn wsgi:app
```

This command is **production-safe by default**: when `APP_CONFIG` is unset, the WSGI entrypoint
(`wsgi.py`) selects the **production** configuration (debug off), so the bare `gunicorn wsgi:app`
command runs with production posture without requiring any extra environment variable. (Development
opts in to development explicitly: `.flaskenv` sets `APP_CONFIG=development`, and the Flask CLI loads
`.flaskenv` for `flask run` — gunicorn does **not** read `.flaskenv`.)

This matches the `Procfile`, which makes the production configuration explicit, binds to all
interfaces, and honors the `PORT` environment variable (defaulting to `5000`):

```text
web: APP_CONFIG=production gunicorn wsgi:app --bind 0.0.0.0:${PORT:-5000}
```

The `PORT` variable therefore controls the production listen port; in development, set the port with
`flask run --port <PORT>` as shown above.

## Configuration

Configuration is supplied entirely through **environment variables**, loaded from a local `.env`
file by `python-dotenv` (the WSGI entrypoint calls `load_dotenv()` at startup). The environment
template (`.env.example`) enumerates these variables. They are consumed through configuration classes
(**Base / Development / Production / Testing**) defined in `app/config.py` and selected by
`APP_CONFIG`. Selection **fails safe to production**: when `APP_CONFIG` is unset the WSGI entrypoint
defaults to the production configuration (so `gunicorn wsgi:app` is safe with debug off), while the
development server opts in via `.flaskenv` (`APP_CONFIG=development`). An unrecognized `APP_CONFIG`
name passed to the factory falls back to the development configuration. The `DEBUG`, `SECRET_KEY`,
`PORT`, and `LOG_LEVEL` variables further override the selected class's values when set in the
environment. **Secrets are never hard-coded** — they live only in your git-ignored `.env`.

The table below mirrors `.env.example` exactly. Copy that template to `.env` and replace the
placeholders with values for your environment.

| Variable      | Example value                  | Required | Description                                                                                   |
| ------------- | ------------------------------ | -------- | --------------------------------------------------------------------------------------------- |
| `FLASK_APP`   | `wsgi.py`                      | Yes      | Import path of the WSGI module exposing the `app` object; lets the Flask CLI locate the app.  |
| `APP_CONFIG`  | `development`                  | No       | Selects the active config class in `app/config.py`: `development`, `production`, or `testing`. When unset, the WSGI entrypoint defaults to `production`; `flask run` selects `development` via `.flaskenv`. |
| `FLASK_DEBUG` | `1`                            | No       | Flask CLI flag enabling the interactive debugger and auto‑reloader for `flask run`. Use `1` in development, `0` in production. |
| `SECRET_KEY`  | `change-me-in-your-local-env`  | Yes (prod) | Key for session signing, CSRF protection, and other signing. Set a strong random value; never commit a real secret. |
| `PORT`        | `5000`                         | No       | TCP port the server listens on (used by the production `Procfile` bind; default `5000`).       |
| `LOG_LEVEL`   | `INFO`                         | No       | Application logging verbosity: `DEBUG`, `INFO`, `WARNING`, or `ERROR`.                          |

To generate a strong `SECRET_KEY` locally:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> **Optional debug override.** An explicit `DEBUG` environment variable overrides the selected
> configuration class's debug flag (accepting `1/true/yes/on` → on and `0/false/no/off` → off). It is
> intentionally **not** an active key in `.env.example` so that, by default, the class default applies
> (`development` on, `production` off). Set it only when you need to force debug on or off independently
> of the selected configuration. Note this is distinct from `FLASK_DEBUG`, which the Flask CLI applies
> to the `flask run` dev server only.

> **Note:** Database, authentication, and CORS variables (e.g. `DATABASE_URL`, `JWT_SECRET`,
> `CORS_ORIGINS`) are **not** part of the baseline scaffold. They will be added here — and mirrored in
> `.env.example` and `app/config.py` — once the original Node.js source establishes that those
> capabilities are required.

## API Endpoints

The API Blueprint is registered at the application root (no `/api` prefix). The scaffold always
exposes a health endpoint:

| Method | Path      | Description                          | Success Status | Response Body        |
| ------ | --------- | ------------------------------------ | -------------- | -------------------- |
| `GET`  | `/health` | Liveness/health check for the server | `200`          | `{"status": "ok"}`   |
| `GET`  | `/good-evening` | User-requested greeting endpoint | `200`          | `Good evening` (plain text) |

> Application‑specific endpoints (the business routes of the original server) are **ported one‑to‑one**
> from the original Node.js routes — preserving method, path, status code, headers, and JSON shape —
> once the original source is supplied. They are intentionally **not** listed here yet to avoid
> documenting behavior that does not exist in the baseline.

## Project Structure

The tree below is the project's **target** layout — the full intended structure of the finished
port, following the idiomatic Flask application-factory pattern. It is **not** the current state:
what exists at this checkpoint versus what is planned for a later milestone is listed immediately
after the tree.

```text
.
├── app/                     # Flask application package
│   ├── __init__.py          # Application factory: create_app() assembles config, extensions,
│   │                        #   blueprints, error handlers, and request hooks
│   ├── config.py            # Env-driven configuration classes (Base/Development/Production/Testing)
│   ├── extensions.py        # Extension singletons initialized via init_app(app)
│   ├── errors.py            # Centralized JSON error handlers (Express error-middleware parity)
│   ├── middleware.py        # before_request/after_request hooks (request logging, headers)
│   └── api/                 # API Blueprint package
│       ├── __init__.py      # Blueprint initializer
│       └── routes.py        # Blueprint views: health endpoint + one view per ported route
├── tests/                   # pytest suite
│   ├── conftest.py          # Fixtures (app, client)
│   ├── test_health.py       # Health endpoint coverage
│   └── test_api.py          # Endpoint parity tests
├── wsgi.py                  # WSGI entrypoint exposing `app = create_app()` (used by gunicorn)
├── requirements.txt         # Pinned runtime dependencies
├── requirements-dev.txt     # Pinned dev/test dependencies (includes runtime via -r)
├── .env.example             # Environment variable template (copy to .env)
├── .flaskenv                # Flask CLI config (FLASK_APP=wsgi.py, dev flags)
├── Procfile                 # Production start command (gunicorn wsgi:app)
├── pyproject.toml           # pytest + lint (ruff) tooling configuration
├── .gitignore               # Python ignores (.venv, __pycache__, .env, ...)
└── README.md                # This file
```

> **What exists now vs. planned.** Present and runnable at this checkpoint: the application factory
> (`app/__init__.py`), the configuration module (`app/config.py`), the `app/api/` Blueprint package
> (`__init__.py` + `routes.py` with `GET /health`), the WSGI entrypoint (`wsgi.py`), `app/errors.py`,
> `app/extensions.py`, and `app/middleware.py`, alongside the configuration, dependency, and tooling
> files at the repository root. The `tests/` package and its baseline parity modules
> (`tests/conftest.py`, `tests/test_health.py`, and `tests/test_api.py`) are **present and passing**.
> Conditional layers — `app/models/`, `app/services/`, `app/schemas/`, `app/auth.py`, `migrations/`,
> `app/templates/`, and `app/static/` — are added only if the original source exercises the
> corresponding capability.

## Testing

The baseline parity test suite is **present and passing**. It uses
**[pytest](https://docs.pytest.org/)** (the replacement for the original project's `jest` / `mocha`),
which is pinned in `requirements-dev.txt`; `pyproject.toml` configures discovery under `tests/`.

The suite lives in the `tests/` package:

- `tests/conftest.py` — shared fixtures (`app`, `client`) built with the testing configuration.
- `tests/test_health.py` — `GET /health` coverage: status code, exact JSON body, and JSON content
  type.
- `tests/test_api.py` — baseline contract tests: the testing configuration is active, health parity,
  the centralized JSON `404`/`405` error envelopes (including the `405` `Allow` header), and the
  `X-Request-ID` middleware header (presence and echo). It also contains a single intentionally
  **skipped** placeholder for the per-route parity tests (see below).

After installing the dev dependencies (`pip install -r requirements-dev.txt`), run the suite from the
repository root:

```bash
pytest
```

or, equivalently:

```bash
python -m pytest
```

Expected result:

```text
9 passed, 1 skipped
```

This count is authoritative for the current scaffold milestone, broken down as **3** tests in
`tests/test_health.py` + **6** active tests in `tests/test_api.py` + **1** intentionally skipped
placeholder in `tests/test_api.py` = **9 passed, 1 skipped**. The single skipped test is the
ported-routes parity placeholder described below.

The active tests assert **parity** for the baseline contract — verifying HTTP status codes, response
headers, and JSON bodies — so that any deviation from the established behavior is caught. The single
skipped test is an intentional placeholder: once the original Node.js source is supplied, it is
replaced with one active test per ported route asserting byte-compatible parity (HTTP method, path,
status code, response headers, and JSON body).

## Migration Mapping (Node.js → Python)

The original `package.json` dependencies translate to Python equivalents as follows. The Python
packages are declared at exact pinned versions in `requirements.txt` / `requirements-dev.txt`, and
each is added only when the original source actually uses the corresponding capability.

| Node.js package        | Python equivalent                  | Purpose                                   |
| ---------------------- | ---------------------------------- | ----------------------------------------- |
| `express`              | `Flask`                            | Routing, request/response handling        |
| `dotenv`               | `python-dotenv`                    | Environment configuration loading         |
| `cors`                 | `flask-cors`                       | Cross‑origin resource sharing             |
| `jsonwebtoken`         | `PyJWT`                            | JWT encode/decode                          |
| `bcrypt`               | `bcrypt` / `passlib`               | Password hashing                          |
| `mongoose`             | `pymongo` (or MongoEngine)         | MongoDB access/ODM                        |
| `sequelize` / `typeorm`| `SQLAlchemy` / `Flask-SQLAlchemy`  | SQL ORM                                    |
| `axios` / `node-fetch` | `requests`                         | Outbound HTTP client                      |
| `joi` / `zod`          | `marshmallow` / `pydantic`         | Schema validation / serialization         |
| `winston` / `morgan`   | `logging` (stdlib) + request hooks | Application & request logging             |
| `jest` / `mocha`       | `pytest`                           | Test framework                            |
| `nodemon`              | `flask run --debug`                | Hot reload during development             |
| `pm2`                  | `gunicorn`                         | Production process serving                |

### Baseline dependency versions

The baseline runtime and test stack is pinned to the following versions (see `requirements.txt` and
`requirements-dev.txt`):

| Package          | Version   | Role                          |
| ---------------- | --------- | ----------------------------- |
| `Flask`          | `3.1.3`   | Core WSGI web framework       |
| `python-dotenv`  | `1.2.2`   | `.env` loading                |
| `gunicorn`       | `26.0.0`  | Production WSGI server        |
| `Werkzeug`       | `3.1.8`   | WSGI utilities (with Flask)   |
| `pytest`         | `9.0.3`   | Test runner (dev/test only)   |
