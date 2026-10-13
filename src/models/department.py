"""Department model for academic department management."""

from src.extensions import db


class Department(db.Model):
    """An academic department containing sections."""

    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    sections = db.relationship(
        "Section",
        back_populates="department",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        """Return the department as a JSON-friendly dictionary."""
        return {"id": self.id, "name": self.name}
