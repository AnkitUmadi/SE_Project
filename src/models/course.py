"""Course and Enrollment models (SAD Section 3.6)."""

from src.extensions import db
from src.models.user import utc_now


class Course(db.Model):
    """Academic course with unique code, credits, faculty and syllabus (SRS-F-008, F-009)."""

    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=4)
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=False, index=True
    )
    faculty_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    syllabus = db.Column(db.Text, nullable=False, default="")

    department = db.relationship("Department", back_populates="courses")
    faculty = db.relationship("User", backref="courses_taught")

    enrollments = db.relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    attendance_records = db.relationship(
        "Attendance", back_populates="course", cascade="all, delete-orphan"
    )
    exam_registrations = db.relationship(
        "ExamRegistration", back_populates="course", cascade="all, delete-orphan"
    )
    eligibility_overrides = db.relationship(
        "EligibilityOverride", back_populates="course", cascade="all, delete-orphan"
    )
    marks = db.relationship("Marks", back_populates="course", cascade="all, delete-orphan")

    def to_dict(self):
        """Serialize course for JSON API responses."""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "credits": self.credits,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "faculty_id": self.faculty_id,
            "faculty_name": self.faculty.name if self.faculty else None,
            "syllabus": self.syllabus or "",
        }


class Enrollment(db.Model):
    """Enrollment linking a student to a course (unique pair, SRS-F-010)."""

    __tablename__ = "enrollments"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
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
    enrolled_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    student = db.relationship("Student", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    def to_dict(self):
        """Serialize enrollment for JSON API responses."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
        }
