"""Unit tests for app settings."""

from src.config import TestConfig


def test_test_config_is_marked_as_testing():
    assert TestConfig.TESTING is True
    assert TestConfig.WTF_CSRF_ENABLED is False


def test_session_lifetime_is_30_minutes():
    assert TestConfig.PERMANENT_SESSION_LIFETIME == 30 * 60
