"""Shared test setup: a fresh app and test client for every test."""

import pytest

from src.app import create_app
from src.config import TestConfig
from src.extensions import db
from src.services.auth_service import create_user

TEST_PASSWORD = "Secret#123"


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


@pytest.fixture
def make_user(app):
    """Create a user in the test database: make_user("faculty") -> User."""

    def _make(role="admin", email=None):
        with app.app_context():
            user = create_user(email or f"{role}@pes.edu", f"Test {role}", TEST_PASSWORD, role)
            db.session.expunge(user)
            return user

    return _make
