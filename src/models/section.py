"""Section model for academic section management."""

from src.extensions import db


class Section(db.Model):
    """A section belonging to exactly one department."""

    __tablename__ = "sections"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False,
    )

    department = db.relationship("Department", back_populates="sections")

    __table_args__ = (
        db.UniqueConstraint(
            "name",
            "department_id",
            name="uq_section_name_department",
        ),
    )

    def to_dict(self):
        """Return the section as a JSON-friendly dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "department_id": self.department_id,
        }
