"""Admin API for managing student semester fee statuses."""

from flask import Blueprint, jsonify, request

from src.extensions import db
from src.models import FeeState, FeeStatus, Student
from src.rbac import admin_required

fees_bp = Blueprint(
    "fees",
    __name__,
    url_prefix="/api/admin/fees",
)


@fees_bp.get("")
@admin_required
def list_fee_statuses():
    """List fee statuses, optionally filtered by semester."""
    query = FeeStatus.query

    semester = request.args.get("semester")
    if semester is not None:
        try:
            semester = int(semester)
        except ValueError:
            return jsonify({"error": "Semester must be an integer."}), 400

        if not 1 <= semester <= 8:
            return jsonify({"error": "Semester must be between 1 and 8."}), 400

        query = query.filter_by(semester=semester)

    records = query.order_by(FeeStatus.student_id, FeeStatus.semester).all()
    return jsonify({"fees": [record.to_dict() for record in records]})


@fees_bp.put("/<int:student_id>")
@admin_required
def set_fee_status(student_id):
    """Create or update a student's fee status for a semester."""
    student = db.session.get(Student, student_id)
    if student is None:
        return jsonify({"error": "Student not found."}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required."}), 400

    semester = data.get("semester")
    status = data.get("status")

    if not isinstance(semester, int) or isinstance(semester, bool) or not 1 <= semester <= 8:
        return jsonify({"error": "Semester must be an integer between 1 and 8."}), 400

    if not isinstance(status, str):
        return jsonify({"error": "Status must be PAID or UNPAID."}), 400

    status = status.strip().upper()
    if status not in FeeState.ALL:
        return jsonify({"error": "Status must be PAID or UNPAID."}), 400

    record = FeeStatus.query.filter_by(
        student_id=student_id,
        semester=semester,
    ).first()

    if record is None:
        record = FeeStatus(
            student_id=student_id,
            semester=semester,
            status=status,
        )
        db.session.add(record)
    else:
        record.status = status

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Could not save fee status."}), 409

    return jsonify({"fee": record.to_dict()})
