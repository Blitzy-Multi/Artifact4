"""Tests for the user-requested greeting endpoint.

Asserts the contract: GET /good-evening returns HTTP 200 with the plain-text
body "Good evening" and a text/plain; charset=utf-8 content type.
"""


def test_good_evening_body(client):
    """GET /good-evening returns 200 with the plain-text body "Good evening"."""
    response = client.get("/good-evening")
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Good evening"
    assert response.content_type == "text/plain; charset=utf-8"
