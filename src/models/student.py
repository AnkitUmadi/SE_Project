"""Department, Section, Student and FeeStatus models (SAD Section 3.6)."""

from src.extensions import db


class FeeState:
    """Allowed values for a student's semester fee status (SRS-F-015)."""

    PAID = "PAID"
    UNPAID = "UNPAID"
    ALL = (PAID, UNPAID)


class Department(db.Model):
    """Academic department (e.g. CSE-AIML, CSE)."""

    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)

    sections = db.relationship("Section", back_populates="department", cascade="all, delete-orphan")
    courses = db.relationship("Course", back_populates="department", cascade="all, delete-orphan")
    students = db.relationship("Student", back_populates="department")

    def to_dict(self):
        """Serialize department for JSON API responses."""
        return {"id": self.id, "name": self.name}


class Section(db.Model):
    """A class section belonging to exactly one department (SRS-F-004)."""

    __tablename__ = "sections"
    __table_args__ = (
        db.UniqueConstraint("department_id", "name", name="uq_section_department_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    department = db.relationship("Department", back_populates="sections")
    students = db.relationship("Student", back_populates="section")

    def to_dict(self):
        """Serialize section for JSON API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
        }


class Student(db.Model):
    """Student record with unique SRN and email (SRS-F-005)."""

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    srn = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    semester = db.Column(db.Integer, nullable=False, default=1)
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=True, index=True
    )
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False, index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=True, index=True
    )

    department = db.relationship("Department", back_populates="students")
    section = db.relationship("Section", back_populates="students")
    user = db.relationship("User", backref=db.backref("student_profile", uselist=False))

    enrollments = db.relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )
    attendance_records = db.relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )
    fee_records = db.relationship(
        "FeeStatus", back_populates="student", cascade="all, delete-orphan"
    )
    exam_registrations = db.relationship(
        "ExamRegistration", back_populates="student", cascade="all, delete-orphan"
    )
    eligibility_overrides = db.relationship(
        "EligibilityOverride", back_populates="student", cascade="all, delete-orphan"
    )
    marks = db.relationship("Marks", back_populates="student", cascade="all, delete-orphan")

    def to_dict(self):
        """Serialize student record for JSON API responses."""
        dept_id = self.department_id or (self.section.department_id if self.section else None)
        dept_name = (
            self.department.name
            if self.department
            else (
                self.section.department.name if self.section and self.section.department else None
            )
        )
        return {
            "id": self.id,
            "srn": self.srn,
            "name": self.name,
            "email": self.email,
            "semester": self.semester,
            "department_id": dept_id,
            "department_name": dept_name,
            "section_id": self.section_id,
            "section_name": self.section.name if self.section else None,
            "user_id": self.user_id,
        }


class FeeStatus(db.Model):
    """Semester fee payment status (PAID / UNPAID) for a student (SRS-F-015)."""

    __tablename__ = "fee_status"
    __table_args__ = (
        db.UniqueConstraint("student_id", "semester", name="uq_fee_student_semester"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    semester = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default=FeeState.UNPAID)

    student = db.relationship("Student", back_populates="fee_records")

    def to_dict(self):
        """Serialize fee status for JSON API responses."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "semester": self.semester,
            "status": self.status,
        }
