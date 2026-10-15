"""Faculty and Student course views with syllabus (SRS-F-009).

Faculty see the courses assigned to them and can edit their syllabus;
Students see the courses they are enrolled in.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from src.models import Course
from src.rbac import faculty_required, student_required
from src.services import course_service
from src.services.course_service import CourseError

my_courses_bp = Blueprint("my_courses", __name__, url_prefix="/api")


@my_courses_bp.errorhandler(CourseError)
def course_error(error):
    """Turn a CourseError from the service into a JSON error response."""
    return jsonify({"error": error.message}), error.status_code


@my_courses_bp.get("/faculty/courses")
@faculty_required
def faculty_courses():
    """Courses taught by the logged-in faculty member."""
    courses = Course.query.filter_by(faculty_id=current_user.id).order_by(Course.code).all()
    return jsonify({"courses": [course.to_dict() for course in courses]})


@my_courses_bp.put("/faculty/courses/<int:course_id>/syllabus")
@faculty_required
def update_syllabus(course_id):
    """The assigned faculty member replaces the course syllabus: {"syllabus": "..."}."""
    course = course_service.get_course(course_id)
    if course.faculty_id != current_user.id:
        raise CourseError("Only the faculty assigned to this course can edit its syllabus.", 403)
    data = request.get_json(silent=True) or {}
    course = course_service.update_syllabus(course, data.get("syllabus"))
    return jsonify({"course": course.to_dict()})


@my_courses_bp.get("/student/courses")
@student_required
def student_courses():
    """Courses the logged-in student is enrolled in, with syllabus."""
    student = course_service.student_for_user(current_user)
    if student is None:
        return jsonify({"courses": []})
    courses = sorted(
        (enrollment.course for enrollment in student.enrollments), key=lambda c: c.code
    )
    return jsonify({"courses": [course.to_dict() for course in courses]})
