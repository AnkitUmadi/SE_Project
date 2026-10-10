"""Shared test setup: a fresh app and test client for every test."""

import pytest

from src.app import create_app
from src.config import TestConfig


@pytest.fixture
def app():
    """App configured for testing (in-memory SQLite)."""
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    """Fake browser for calling the API in tests."""
    return app.test_client()
