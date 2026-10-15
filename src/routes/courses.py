"""Admin API for courses, syllabus and enrollment (SRS-F-008, F-009, F-010)."""

from flask import Blueprint, jsonify, request

from src.models import Course
from src.rbac import admin_required
from src.services import course_service
from src.services.course_service import CourseError

courses_bp = Blueprint("courses", __name__, url_prefix="/api/admin")


@courses_bp.errorhandler(CourseError)
def course_error(error):
    """Turn a CourseError from the service into a JSON error response."""
    return jsonify({"error": error.message}), error.status_code


@courses_bp.get("/courses")
@admin_required
def list_courses():
    """List all courses, optionally filtered by ?search= on code or name."""
    query = Course.query
    search = (request.args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(Course.code.ilike(pattern) | Course.name.ilike(pattern))
    courses = query.order_by(Course.code).all()
    return jsonify({"courses": [course.to_dict() for course in courses]})


@courses_bp.post("/courses")
@admin_required
def create_course():
    """Create a course. Duplicate course codes get HTTP 409."""
    course = course_service.create_course(request.get_json(silent=True))
    return jsonify({"course": course.to_dict()}), 201


@courses_bp.get("/courses/<int:course_id>")
@admin_required
def get_course(course_id):
    """One course, including its syllabus."""
    return jsonify({"course": course_service.get_course(course_id).to_dict()})


@courses_bp.put("/courses/<int:course_id>")
@admin_required
def update_course(course_id):
    """Update any course fields, including the syllabus."""
    course = course_service.update_course(course_id, request.get_json(silent=True))
    return jsonify({"course": course.to_dict()})


@courses_bp.delete("/courses/<int:course_id>")
@admin_required
def delete_course(course_id):
    """Delete a course and everything recorded for it."""
    course_service.delete_course(course_id)
    return jsonify({"message": "Course deleted."})


@courses_bp.get("/faculty")
@admin_required
def list_faculty():
    """Faculty members, for the course form's dropdown."""
    return jsonify({"faculty": [user.to_dict() for user in course_service.list_faculty()]})


@courses_bp.get("/courses/<int:course_id>/enrollments")
@admin_required
def list_enrollments(course_id):
    """The course roster: every enrolled student."""
    course = course_service.get_course(course_id)
    students = course_service.course_roster(course)
    return jsonify({"students": [student.to_dict() for student in students]})


@courses_bp.post("/courses/<int:course_id>/enrollments")
@admin_required
def enroll_students(course_id):
    """Enroll students: {"student_ids": [..]}. Already enrolled -> HTTP 409, nothing saved."""
    data = request.get_json(silent=True) or {}
    students = course_service.enroll_students(course_id, data.get("student_ids"))
    return jsonify({"enrolled": [student.to_dict() for student in students]}), 201


@courses_bp.delete("/courses/<int:course_id>/enrollments/<int:student_id>")
@admin_required
def unenroll_student(course_id, student_id):
    """Remove a student from the course."""
    course_service.unenroll_student(course_id, student_id)
    return jsonify({"message": "Student removed from course."})
