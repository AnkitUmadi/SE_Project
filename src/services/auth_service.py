"""Login rules: check the password, count failures, lock the account (F-001, F-003, SR-003)."""

from datetime import timedelta

from src.extensions import db
from src.models.user import Role, User, utc_now

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15
LOCKED_MESSAGE = (
    f"Account locked after {MAX_FAILED_LOGINS} failed logins. "
    f"Try again in {LOCK_MINUTES} minutes."
)


class AuthError(Exception):
    """A login problem, with the HTTP status code the API should return."""

    status_code = 401

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class InvalidCredentials(AuthError):
    """Wrong email or password. Same message for both on purpose,
    so an attacker cannot find out which emails exist."""

    status_code = 401


class AccountLocked(AuthError):
    """Too many failed logins; the account is locked for a while."""

    status_code = 423


def authenticate(email, password, now=None):
    """Return the User if email and password are correct, otherwise raise an AuthError.

    `now` can be passed in by tests to pretend time has moved on.
    """
    now = now or utc_now()
    user = User.query.filter_by(email=(email or "").strip().lower()).first()
    if user is None:
        raise InvalidCredentials("Invalid email or password.")

    if user.is_locked(now):
        raise AccountLocked(LOCKED_MESSAGE)

    if not user.check_password(password or ""):
        user.failed_logins += 1
        if user.failed_logins >= MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
            user.failed_logins = 0
            db.session.commit()
            raise AccountLocked(LOCKED_MESSAGE)
        db.session.commit()
        raise InvalidCredentials("Invalid email or password.")

    user.failed_logins = 0
    user.locked_until = None
    db.session.commit()
    return user


def create_user(email, name, password, role):
    """Create and save a user with a hashed password. Used by scripts and tests."""
    if role not in Role.ALL:
        raise ValueError(f"Role must be one of {', '.join(Role.ALL)}, not '{role}'.")
    user = User(email=email.strip().lower(), name=name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user
