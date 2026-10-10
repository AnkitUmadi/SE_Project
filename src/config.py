"""App settings. Real values come from the .env file (never committed)."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Settings used when running the app normally (MySQL)."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.sqlite")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 30 * 60  # 30 minutes (SRS-F-003)
    TESTING = False


class TestConfig(Config):
    """Settings for automated tests: fast in-memory SQLite database."""

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    WTF_CSRF_ENABLED = False  # individual security tests switch it back on
