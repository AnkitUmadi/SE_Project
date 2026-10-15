"""Course, syllabus and enrollment rules (CourseModule in the SAD; SRS-F-008, F-009, F-010)."""

from src.extensions import db
from src.models import Course, Department, Enrollment, Role, Student, User
from src.services.seed_service import atomic_transaction

MIN_CREDITS = 1
MAX_CREDITS = 6
MAX_CODE_LENGTH = 30
MAX_NAME_LENGTH = 120


class CourseError(Exception):
    """A course or enrollment problem, with the HTTP status code the API should return."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _is_int(value):
    """True for real integers (JSON true/false are not accepted as numbers)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _clean_text(value, label, max_length):
    """Return the stripped text, or raise if it is missing or too long."""
    if not isinstance(value, str) or not value.strip():
        raise CourseError(f"{label} is required.")
    value = value.strip()
    if len(value) > max_length:
        raise CourseError(f"{label} must be at most {max_length} characters.")
    return value


def _check_faculty(faculty_id):
    """A course may have no faculty yet; otherwise it must be a Faculty user."""
    if faculty_id is None:
        return None
    if not _is_int(faculty_id):
        raise CourseError("A valid faculty_id is required.")
    faculty = db.session.get(User, faculty_id)
    if faculty is None or faculty.role != Role.FACULTY:
        raise CourseError("Selected faculty member not found.", 404)
    return faculty_id


def validate_course_data(data, existing=None):
    """Check course fields (new course, or a partial update of `existing`) and return clean values.

    Raises CourseError on invalid input or a duplicate course code.
    """
    if not isinstance(data, dict):
        raise CourseError("A JSON object is required.")

    def field(name):
        return data.get(name, getattr(existing, name) if existing else None)

    code = _clean_text(field("code"), "Course code", MAX_CODE_LENGTH).upper()
    name = _clean_text(field("name"), "Course name", MAX_NAME_LENGTH)

    credit_count = field("credits")
    if not _is_int(credit_count) or not MIN_CREDITS <= credit_count <= MAX_CREDITS:
        raise CourseError(f"Credits must be a whole number from {MIN_CREDITS} to {MAX_CREDITS}.")

    department_id = field("department_id")
    if not _is_int(department_id):
        raise CourseError("A valid department_id is required.")
    if db.session.get(Department, department_id) is None:
        raise CourseError("Department not found.", 404)

    faculty_id = _check_faculty(field("faculty_id"))

    syllabus = field("syllabus")
    if syllabus is None:
        syllabus = ""
    if not isinstance(syllabus, str):
        raise CourseError("Syllabus must be text.")

    duplicate = Course.query.filter(
        Course.code == code, Course.id != (existing.id if existing else -1)
    ).first()
    if duplicate:
        raise CourseError(f"Course code {code} already exists.", 409)

    return {
        "code": code,
        "name": name,
        "credits": credit_count,
        "department_id": department_id,
        "faculty_id": faculty_id,
        "syllabus": syllabus.strip(),
    }


def get_course(course_id):
    """Return the course or raise a 404 CourseError."""
    course = db.session.get(Course, course_id)
    if course is None:
        raise CourseError("Course not found.", 404)
    return course


def create_course(data):
    """Validate and save a new course."""
    course = Course(**validate_course_data(data))
    with atomic_transaction():
        db.session.add(course)
    return course


def update_course(course_id, data):
    """Validate and apply a (partial) update to a course."""
    course = get_course(course_id)
    values = validate_course_data(data, existing=course)
    with atomic_transaction():
        for name, value in values.items():
            setattr(course, name, value)
    return course


def delete_course(course_id):
    """Delete a course with its enrollments and other course records."""
    course = get_course(course_id)
    with atomic_transaction():
        db.session.delete(course)


def update_syllabus(course, syllabus):
    """Replace a course's syllabus text (SRS-F-009)."""
    if not isinstance(syllabus, str):
        raise CourseError("Syllabus must be text.")
    with atomic_transaction():
        course.syllabus = syllabus.strip()
    return course


def list_faculty():
    """All Faculty users, for the course form's faculty dropdown."""
    return User.query.filter_by(role=Role.FACULTY).order_by(User.name).all()


def course_roster(course):
    """Students enrolled in the course, ordered by SRN."""
    return (
        Student.query.join(Enrollment, Enrollment.student_id == Student.id)
        .filter(Enrollment.course_id == course.id)
        .order_by(Student.srn)
        .all()
    )


def enroll_students(course_id, student_ids):
    """Enroll one or more students in a course, all or nothing (SRS-F-010, NF-005).

    A student who is already enrolled is rejected with HTTP 409 and nothing is saved.
    """
    course = get_course(course_id)
    if (
        not isinstance(student_ids, list)
        or not student_ids
        or not all(_is_int(student_id) for student_id in student_ids)
    ):
        raise CourseError("student_ids must be a non-empty list of student ids.")
    if len(set(student_ids)) != len(student_ids):
        raise CourseError("The same student is listed more than once.")

    students = []
    for student_id in student_ids:
        student = db.session.get(Student, student_id)
        if student is None:
            raise CourseError(f"Student {student_id} not found.", 404)
        already = Enrollment.query.filter_by(student_id=student_id, course_id=course.id).first()
        if already:
            raise CourseError(
                f"{student.srn} is already enrolled in {course.code}.",
                409,
            )
        students.append(student)

    with atomic_transaction():
        for student in students:
            db.session.add(Enrollment(student_id=student.id, course_id=course.id))
    return students


def unenroll_student(course_id, student_id):
    """Remove a student from a course."""
    course = get_course(course_id)
    enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course.id).first()
    if enrollment is None:
        raise CourseError("Student is not enrolled in this course.", 404)
    with atomic_transaction():
        db.session.delete(enrollment)


def student_for_user(user):
    """The Student record linked to a logged-in Student user, or None."""
    return Student.query.filter_by(user_id=user.id).first()
