"""Attendance model (SAD Section 3.6)."""

from src.extensions import db


class Attendance(db.Model):
    """Per-date attendance entry for a student in a course (SRS-F-011, F-012)."""

    __tablename__ = "attendance"
    __table_args__ = (
        db.UniqueConstraint(
            "course_id", "student_id", "date", name="uq_attendance_course_student_date"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = db.Column(db.Date, nullable=False, index=True)
    present = db.Column(db.Boolean, nullable=False, default=True)

    course = db.relationship("Course", back_populates="attendance_records")
    student = db.relationship("Student", back_populates="attendance_records")

    def to_dict(self):
        """Serialize attendance entry for JSON API responses."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "student_id": self.student_id,
            "date": self.date.isoformat() if self.date else None,
            "present": self.present,
        }
