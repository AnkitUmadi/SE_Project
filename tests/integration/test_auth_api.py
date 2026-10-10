"""Integration tests for the login API: Flask + database + session cookie together."""

from datetime import timedelta

import pytest

from src.app import create_app
from src.config import TestConfig
from src.extensions import db
from src.services.auth_service import MAX_FAILED_LOGINS
from tests.conftest import TEST_PASSWORD


def login(client, email, password=TEST_PASSWORD):
    """Helper: call the login API."""
    return client.post("/api/auth/login", json={"email": email, "password": password})


@pytest.mark.parametrize("role", ["admin", "faculty", "student"])
def test_tc_auth_01_valid_login_returns_role(client, make_user, role):
    make_user(role)
    response = login(client, f"{role}@pes.edu")
    assert response.status_code == 200
    assert response.get_json()["user"]["role"] == role
    # The session cookie now identifies the user
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["user"]["email"] == f"{role}@pes.edu"


def test_tc_auth_02_wrong_password_gives_401_and_no_session(client, make_user):
    make_user("admin")
    response = login(client, "admin@pes.edu", "wrong-password")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid email or password."
    assert client.get("/api/auth/me").status_code == 401


def test_missing_fields_give_400(client):
    assert client.post("/api/auth/login", json={"email": "a@pes.edu"}).status_code == 400
    assert client.post("/api/auth/login", data="not json").status_code == 400


def test_tc_sec_03_five_failures_give_423(client, make_user):
    make_user("faculty")
    for _ in range(MAX_FAILED_LOGINS - 1):
        assert login(client, "faculty@pes.edu", "wrong-password").status_code == 401
    assert login(client, "faculty@pes.edu", "wrong-password").status_code == 423
    assert login(client, "faculty@pes.edu").status_code == 423


def test_tc_auth_04_logout_ends_session(client, make_user):
    make_user("student")
    login(client, "student@pes.edu")
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_logout_without_login_gives_401_json(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 401
    assert "error" in response.get_json()


def test_tc_auth_04_session_expires_after_30_minutes(app, client, make_user):
    make_user("admin")
    login(client, "admin@pes.edu")
    with client.session_transaction() as session:
        assert session.permanent is True
    assert app.permanent_session_lifetime == timedelta(minutes=30)


def test_login_requires_csrf_token_when_protection_is_on():
    class CsrfOnConfig(TestConfig):
        WTF_CSRF_ENABLED = True

    app = create_app(CsrfOnConfig)
    client = app.test_client()
    try:
        no_token = client.post("/api/auth/login", json={"email": "a@pes.edu", "password": "x"})
        assert no_token.status_code == 400

        token = client.get("/api/auth/csrf").get_json()["csrf_token"]
        with_token = client.post(
            "/api/auth/login",
            json={"email": "a@pes.edu", "password": "x"},
            headers={"X-CSRFToken": token},
        )
        assert with_token.status_code == 401  # token accepted; user simply doesn't exist
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
