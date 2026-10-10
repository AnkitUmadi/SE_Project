"""The users table: everyone who can log in (Admin, Faculty, Student)."""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from src.extensions import db, login_manager


def utc_now():
    """Current time in UTC without timezone info (MySQL DATETIME stores no timezone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Role:
    """The three roles from the SRS."""

    ADMIN = "admin"
    FACULTY = "faculty"
    STUDENT = "student"
    ALL = (ADMIN, FACULTY, STUDENT)


class User(UserMixin, db.Model):
    """A person who can log in. The password is stored only as a salted hash (SR-001)."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    failed_logins = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    def set_password(self, password):
        """Store a one-way salted hash of the password, never the password itself."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """True if the password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_locked(self, now=None):
        """True while the account is locked after too many failed logins (SR-003)."""
        now = now or utc_now()
        return self.locked_until is not None and self.locked_until > now

    def to_dict(self):
        """Safe public view of the user (no password hash)."""
        return {"id": self.id, "email": self.email, "name": self.name, "role": self.role}


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login calls this on every request to turn the session's user id into a User."""
    return db.session.get(User, int(user_id))
