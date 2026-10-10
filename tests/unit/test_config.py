"""Unit tests for app settings."""

from src.config import TestConfig


def test_test_config_uses_in_memory_sqlite():
    assert TestConfig.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"
    assert TestConfig.TESTING is True


def test_session_lifetime_is_30_minutes():
    assert TestConfig.PERMANENT_SESSION_LIFETIME == 30 * 60
