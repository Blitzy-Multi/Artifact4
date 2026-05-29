"""Shared pytest fixtures for the Flask test suite.

Provides the ``app`` fixture (an application instance built with the Testing
configuration) and the ``client`` fixture (a Flask test client) used across the
parity tests. Tests rely on the application factory ``create_app`` exported by
the ``app`` package.
"""
import pytest

from app import create_app


@pytest.fixture
def app():
    """Build a fresh application instance configured for testing."""
    application = create_app("testing")
    yield application


@pytest.fixture
def client(app):
    """Return a Flask test client for issuing requests against the app."""
    return app.test_client()
