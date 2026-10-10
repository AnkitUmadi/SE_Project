"""Health check: lets the frontend and CI confirm the backend is running."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health():
    """Return a simple status message."""
    return jsonify({"status": "ok", "service": "student-record-system"})
