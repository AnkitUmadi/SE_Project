"""ESA exam window, registration and eligibility override models (SAD Section 3.6)."""

from src.extensions import db
from src.models.user import utc_now


class ExamWindow(db.Model):
    """Tracks whether the ESA registration window is currently open (SRS-F-016)."""

    __tablename__ = "exam_window"

    id = db.Column(db.Integer, primary_key=True)
    is_open = db.Column(db.Boolean, nullable=False, default=False)
    opened_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        """Serialize exam window state for JSON API responses."""
        return {
            "id": self.id,
            "is_open": self.is_open,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }


class ExamRegistration(db.Model):
    """Student registration for a course's End-Semester Assessment (SRS-F-017)."""

    __tablename__ = "exam_registrations"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="uq_exam_reg_student_course"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    registered_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    student = db.relationship("Student", back_populates="exam_registrations")
    course = db.relationship("Course", back_populates="exam_registrations")

    def to_dict(self):
        """Serialize exam registration for JSON API responses."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "registered_at": (self.registered_at.isoformat() if self.registered_at else None),
        }


class EligibilityOverride(db.Model):
    """Admin override allowing a student to register for an ESA with a reason (SRS-F-026)."""

    __tablename__ = "eligibility_overrides"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="uq_override_student_course"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reason = db.Column(db.String(255), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    student = db.relationship("Student", back_populates="eligibility_overrides")
    course = db.relationship("Course", back_populates="eligibility_overrides")
    admin = db.relationship("User")

    def to_dict(self):
        """Serialize eligibility override for JSON API responses."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "reason": self.reason,
            "admin_id": self.admin_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
