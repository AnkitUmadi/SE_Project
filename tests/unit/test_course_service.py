"""Unit tests for course, syllabus and enrollment rules (Issues #11, #12)."""

import pytest

from src.extensions import db
from src.models import Course, Department, Enrollment, Section, Student
from src.services import course_service
from src.services.auth_service import create_user
from src.services.course_service import CourseError
from tests.conftest import TEST_PASSWORD


@pytest.fixture
def ctx(app):
    """An app context with one department, one section and two students."""
    with app.app_context():
        department = Department(name="CSE-AIML")
        db.session.add(department)
        db.session.flush()
        section = Section(name="H", department_id=department.id)
        db.session.add(section)
        db.session.flush()
        for index in (1, 2):
            db.session.add(
                Student(
                    srn=f"PES1UG24AM{index:03d}",
                    name=f"Student {index}",
                    email=f"s{index}@pes.edu",
                    semester=4,
                    department_id=department.id,
                    section_id=section.id,
                )
            )
        db.session.commit()
        yield department


def valid(department, **overrides):
    """A valid course payload."""
    data = {"code": "ue24am241a", "name": " Software Engineering ", "credits": 4}
    data["department_id"] = department.id
    data.update(overrides)
    return data


def test_tc_crs_01_validate_cleans_values_and_rejects_duplicate_code(ctx):
    """TC-CRS-01 (unit): code upper-cased, text trimmed; an existing code is a 409."""
    values = course_service.validate_course_data(valid(ctx))
    assert values["code"] == "UE24AM241A"
    assert values["name"] == "Software Engineering"
    assert values["syllabus"] == ""
    assert values["faculty_id"] is None

    course_service.create_course(valid(ctx))
    with pytest.raises(CourseError) as error:
        course_service.validate_course_data(valid(ctx, name="Copy"))
    assert error.value.status_code == 409


def test_update_keeps_own_code_and_unchanged_fields(ctx):
    """A partial update keeps the course's other values and may keep its own code."""
    course = course_service.create_course(valid(ctx, syllabus="Unit 1"))
    updated = course_service.update_course(course.id, {"name": "SE", "code": "UE24AM241A"})
    assert (updated.name, updated.code, updated.credits, updated.syllabus) == (
        "SE",
        "UE24AM241A",
        4,
        "Unit 1",
    )


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"code": None}, "Course code is required."),
        ({"code": "X" * 31}, "Course code must be at most 30 characters."),
        ({"name": ""}, "Course name is required."),
        ({"credits": 0}, "Credits must be a whole number from 1 to 6."),
        ({"credits": 6.5}, "Credits must be a whole number from 1 to 6."),
        ({"department_id": None}, "A valid department_id is required."),
        ({"faculty_id": "1"}, "A valid faculty_id is required."),
        ({"syllabus": ["Unit 1"]}, "Syllabus must be text."),
    ],
)
def test_invalid_course_values_have_clear_messages(ctx, overrides, message):
    """Each invalid field is rejected with a message the user understands (SR-007)."""
    with pytest.raises(CourseError) as error:
        course_service.validate_course_data(valid(ctx, **overrides))
    assert error.value.message == message
    assert error.value.status_code == 400


def test_non_dict_payload_is_rejected(ctx):  # pylint: disable=unused-argument
    """The request body must be a JSON object."""
    with pytest.raises(CourseError):
        course_service.validate_course_data(["not", "a", "dict"])


def test_faculty_must_have_faculty_role(ctx):
    """Only Faculty users can be assigned to a course."""
    faculty = create_user("f1@pes.edu", "Dr. F", TEST_PASSWORD, "faculty")
    admin = create_user("a1@pes.edu", "Admin", TEST_PASSWORD, "admin")
    assert course_service.validate_course_data(valid(ctx, faculty_id=faculty.id))["faculty_id"]
    with pytest.raises(CourseError) as error:
        course_service.validate_course_data(valid(ctx, faculty_id=admin.id))
    assert error.value.status_code == 404
    assert [user.email for user in course_service.list_faculty()] == ["f1@pes.edu"]


def test_update_syllabus_trims_text_and_rejects_non_text(ctx):
    """SRS-F-009: syllabus is stored as plain text."""
    course = course_service.create_course(valid(ctx))
    assert course_service.update_syllabus(course, "  Unit 1: SRS  ").syllabus == "Unit 1: SRS"
    with pytest.raises(CourseError):
        course_service.update_syllabus(course, None)


def test_tc_crs_03_enroll_once_then_duplicate_is_409(ctx):
    """TC-CRS-03 (unit): a student cannot be enrolled twice in the same course."""
    course = course_service.create_course(valid(ctx))
    first, second = [student.id for student in Student.query.order_by(Student.srn)]

    course_service.enroll_students(course.id, [first])
    assert [s.id for s in course_service.course_roster(course)] == [first]

    with pytest.raises(CourseError) as error:
        course_service.enroll_students(course.id, [second, first])
    assert error.value.status_code == 409
    assert "PES1UG24AM001 is already enrolled in UE24AM241A" in error.value.message
    assert Enrollment.query.count() == 1


def test_unenroll_and_delete_course(ctx):
    """Removing an enrollment and deleting a course both work; missing ones are 404s."""
    course = course_service.create_course(valid(ctx))
    student_id = Student.query.first().id
    course_service.enroll_students(course.id, [student_id])

    course_service.unenroll_student(course.id, student_id)
    assert Enrollment.query.count() == 0
    with pytest.raises(CourseError) as error:
        course_service.unenroll_student(course.id, student_id)
    assert error.value.status_code == 404

    course_service.delete_course(course.id)
    assert Course.query.count() == 0
    with pytest.raises(CourseError):
        course_service.get_course(course.id)


def test_student_for_user_finds_linked_record(ctx):  # pylint: disable=unused-argument
    """A Student login maps to its student record, or None if not linked."""
    user = create_user("s1@pes.edu", "Student 1", TEST_PASSWORD, "student")
    assert course_service.student_for_user(user) is None
    student = Student.query.filter_by(srn="PES1UG24AM001").first()
    student.user_id = user.id
    db.session.commit()
    assert course_service.student_for_user(user).id == student.id
