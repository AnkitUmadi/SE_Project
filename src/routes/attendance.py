"""Faculty API for marking and correcting attendance (SRS-F-011, F-012)."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from src.rbac import faculty_required
from src.services import attendance_service
from src.services.attendance_service import AttendanceError
from src.services.course_service import CourseError, get_course

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/faculty/attendance")


@attendance_bp.errorhandler(AttendanceError)
@attendance_bp.errorhandler(CourseError)
def attendance_error(error):
    """Turn a service error into a JSON error response."""
    return jsonify({"error": error.message}), error.status_code


@attendance_bp.get("/<int:course_id>")
@faculty_required
def get_attendance(course_id):
    """Enrolled students and their attendance for ?date=YYYY-MM-DD (unsaved = present)."""
    course = get_course(course_id)
    attendance_service.check_assigned_faculty(course, current_user)
    class_date = attendance_service.parse_class_date(request.args.get("date"))
    result = attendance_service.class_attendance(course, class_date)
    return jsonify({"course": course.to_dict(), "date": class_date.isoformat(), **result})


@attendance_bp.put("/<int:course_id>")
@faculty_required
def save_attendance(course_id):
    """Save attendance: {"date": "YYYY-MM-DD", "records": [{"student_id": 1, "present": true}]}."""
    course = get_course(course_id)
    attendance_service.check_assigned_faculty(course, current_user)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise AttendanceError("A JSON object is required.")
    class_date = attendance_service.parse_class_date(data.get("date"))
    saved, corrected = attendance_service.save_attendance(
        course, current_user, class_date, data.get("records")
    )
    return jsonify({"date": class_date.isoformat(), "saved": saved, "corrected": corrected})
