"""Endpoint parity tests mirroring the original server's observable behavior.

These tests assert the API contract (HTTP method, path, status code, response
headers, and JSON shape) that the Flask port must preserve relative to the
original Node.js server. Because the original Node.js source is not yet present
in the repository, this module currently covers the always-present health
endpoint plus the baseline error-handling and middleware behavior, and provides
a clearly-marked placeholder for the routes that will be ported one-to-one once
the original source is supplied. Do NOT assert behavior for endpoints the
original does not expose (AAP 0.1.1, 0.6.2).
"""
import pytest


def test_testing_config_active(app):
    """The app fixture is constructed with the Testing configuration."""
    assert app.config["TESTING"] is True


def test_health_parity(client):
    """Health route parity: GET /health -> 200 with JSON {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_unknown_route_returns_json_404(client):
    """Unknown paths return 404 with the centralized JSON error shape."""
    response = client.get("/__definitely_not_a_real_route__")
    assert response.status_code == 404
    assert response.is_json
    body = response.get_json()
    assert "error" in body
    assert "message" in body


def test_method_not_allowed_returns_405(client):
    """A wrong HTTP method on an existing route returns 405 with JSON error.

    The centralized 405 handler must also preserve the ``Allow`` header that
    Werkzeug attaches to ``MethodNotAllowed`` so clients still learn which
    methods the route supports (HTTP contract; regression guard for the custom
    JSON error handler dropping protocol headers).
    """
    response = client.post("/health")
    assert response.status_code == 405
    assert response.is_json
    body = response.get_json()
    assert "error" in body
    assert "message" in body
    # The Allow header must survive the JSON error envelope and advertise the
    # supported method(s) for the route (GET is defined on /health).
    assert "Allow" in response.headers
    assert "GET" in response.headers["Allow"]


def test_correlation_id_header_present(client):
    """Responses carry the X-Request-ID correlation header (middleware parity)."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers


def test_correlation_id_header_is_echoed(client):
    """An inbound X-Request-ID header is echoed back on the response."""
    correlation_id = "test-correlation-id-123"
    response = client.get("/health", headers={"X-Request-ID": correlation_id})
    assert response.headers.get("X-Request-ID") == correlation_id


# ---------------------------------------------------------------------------
# Placeholder for ported-route parity tests.
#
# Once the original Node.js source is supplied, add one test per ported route
# asserting byte-compatible parity (HTTP method, path, status code, response
# headers, and JSON body). Until then this placeholder is skipped so the suite
# does not assert behavior for endpoints that do not yet exist.
# ---------------------------------------------------------------------------
@pytest.mark.skip(reason="Pending original Node.js source: port each route with byte-compatible parity (method, path, status, headers, JSON).")
def test_ported_routes_parity_placeholder():
    """Placeholder for one-to-one parity tests of the ported routes."""
