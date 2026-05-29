"""Tests for the always-present health endpoint.

Asserts the baseline contract: GET /health returns HTTP 200 with the JSON
body {"status": "ok"} and an application/json content type.
"""


def test_health_status_code(client):
    """GET /health returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_json_body(client):
    """GET /health returns the exact JSON body {"status": "ok"}."""
    response = client.get("/health")
    assert response.get_json() == {"status": "ok"}


def test_health_content_type_is_json(client):
    """GET /health responds with the application/json content type."""
    response = client.get("/health")
    assert response.is_json
    assert response.content_type == "application/json"
