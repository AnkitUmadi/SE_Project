"""Audit log model recording changes to marks, attendance, fees and overrides (SAD Section 3.6)."""

from src.extensions import db
from src.models.user import utc_now


class AuditLog(db.Model):
    """Immutable audit trail entry for state changes (SRS-F-025)."""

    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)

    user = db.relationship("User")

    def to_dict(self):
        """Serialize audit log entry for JSON API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user.email if self.user else None,
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
