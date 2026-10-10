"""Shared test setup: a fresh app and test client for every test."""

import pytest

from src.app import create_app
from src.config import TestConfig
from src.extensions import db


@pytest.fixture
def app():
    """App configured for testing; tables are removed after each test."""
    application = create_app(TestConfig)
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Fake browser for calling the API in tests."""
    return app.test_client()
