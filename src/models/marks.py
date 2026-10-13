"""Marks model storing ISA-1, ISA-2, Assessment, ESA, total and grade (SAD Section 3.6)."""

from src.extensions import db


class Marks(db.Model):
    """Component marks, computed total (/100), PES grade and grade point (SRS-F-019, F-020)."""

    __tablename__ = "marks"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="uq_marks_student_course"),
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
    isa1 = db.Column(db.Float, nullable=True)
    isa2 = db.Column(db.Float, nullable=True)
    assessment = db.Column(db.Float, nullable=True)
    esa = db.Column(db.Float, nullable=True)
    total = db.Column(db.Float, nullable=True)
    grade = db.Column(db.String(5), nullable=True)
    grade_point = db.Column(db.Integer, nullable=True)

    student = db.relationship("Student", back_populates="marks")
    course = db.relationship("Course", back_populates="marks")

    def to_dict(self):
        """Serialize marks record for JSON API responses."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "isa1": self.isa1,
            "isa2": self.isa2,
            "assessment": self.assessment,
            "esa": self.esa,
            "total": self.total,
            "grade": self.grade,
            "grade_point": self.grade_point,
        }


Mark = Marks
