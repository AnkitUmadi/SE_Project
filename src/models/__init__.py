"""Database models (SQLAlchemy) for all tables in SAD Section 3.6.

Every model is imported here so db.create_all() registers its table.
"""

from src.models.attendance import Attendance
from src.models.audit import AuditLog
from src.models.course import Course, Enrollment
from src.models.exam import EligibilityOverride, ExamRegistration, ExamWindow
from src.models.marks import Mark, Marks
from src.models.student import Department, FeeState, FeeStatus, Section, Student
from src.models.user import Role, User, utc_now

__all__ = [
    "Attendance",
    "AuditLog",
    "Course",
    "Department",
    "EligibilityOverride",
    "Enrollment",
    "ExamRegistration",
    "ExamWindow",
    "FeeState",
    "FeeStatus",
    "Mark",
    "Marks",
    "Role",
    "Section",
    "Student",
    "User",
    "utc_now",
]
