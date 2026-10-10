"""Unit tests for the login rules (AuthService). Test case IDs are from the Test Plan."""

from datetime import timedelta

import pytest

from src.extensions import db
from src.models.user import User, utc_now
from src.services.auth_service import (
    LOCK_MINUTES,
    MAX_FAILED_LOGINS,
    AccountLocked,
    InvalidCredentials,
    authenticate,
    create_user,
)
from tests.conftest import TEST_PASSWORD


def test_tc_sec_01_password_is_stored_as_hash(app, make_user):
    make_user("admin")
    with app.app_context():
        user = User.query.filter_by(email="admin@pes.edu").one()
        assert user.password_hash != TEST_PASSWORD
        assert TEST_PASSWORD not in user.password_hash
        assert user.check_password(TEST_PASSWORD)
        assert not user.check_password("wrong-password")


def test_tc_auth_01_correct_password_returns_user(app, make_user):
    make_user("faculty")
    with app.app_context():
        user = authenticate("faculty@pes.edu", TEST_PASSWORD)
        assert user.role == "faculty"


def test_email_is_not_case_sensitive(app, make_user):
    make_user("student")
    with app.app_context():
        assert authenticate("  Student@PES.edu ", TEST_PASSWORD).role == "student"


def test_tc_auth_02_wrong_password_is_rejected(app, make_user):
    make_user("admin")
    with app.app_context():
        with pytest.raises(InvalidCredentials):
            authenticate("admin@pes.edu", "wrong-password")
        assert User.query.filter_by(email="admin@pes.edu").one().failed_logins == 1


def test_unknown_email_gives_same_error_as_wrong_password(app):
    with app.app_context():
        with pytest.raises(InvalidCredentials) as error:
            authenticate("nobody@pes.edu", TEST_PASSWORD)
        assert error.value.message == "Invalid email or password."


def test_tc_sec_03_account_locks_after_5_failures(app, make_user):
    make_user("admin")
    with app.app_context():
        for _ in range(MAX_FAILED_LOGINS - 1):
            with pytest.raises(InvalidCredentials):
                authenticate("admin@pes.edu", "wrong-password")
        with pytest.raises(AccountLocked):
            authenticate("admin@pes.edu", "wrong-password")
        # Even the correct password is refused while locked
        with pytest.raises(AccountLocked):
            authenticate("admin@pes.edu", TEST_PASSWORD)


def test_lock_ends_after_15_minutes(app, make_user):
    make_user("admin")
    with app.app_context():
        now = utc_now()
        for _ in range(MAX_FAILED_LOGINS):
            with pytest.raises((InvalidCredentials, AccountLocked)):
                authenticate("admin@pes.edu", "wrong-password", now=now)
        later = now + timedelta(minutes=LOCK_MINUTES, seconds=1)
        assert authenticate("admin@pes.edu", TEST_PASSWORD, now=later).role == "admin"


def test_successful_login_resets_failure_count(app, make_user):
    make_user("admin")
    with app.app_context():
        with pytest.raises(InvalidCredentials):
            authenticate("admin@pes.edu", "wrong-password")
        authenticate("admin@pes.edu", TEST_PASSWORD)
        assert db.session.get(User, 1).failed_logins == 0


def test_create_user_rejects_unknown_role(app):
    with app.app_context():
        with pytest.raises(ValueError):
            create_user("x@pes.edu", "X", TEST_PASSWORD, "superuser")


def test_to_dict_never_contains_password(app, make_user):
    make_user("student")
    with app.app_context():
        data = User.query.one().to_dict()
        assert set(data) == {"id", "email", "name", "role"}
