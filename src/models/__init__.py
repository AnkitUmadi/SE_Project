"""Database models (SQLAlchemy).

Every model must be imported here so db.create_all() knows about its table.
User is added in issue #3 (login); the other tables are added in issue #4.
"""

from src.models.user import Role, User

__all__ = ["Role", "User"]
