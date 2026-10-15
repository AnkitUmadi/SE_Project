"""Integration tests for marking and correcting attendance (Issue #13)."""

from datetime import date, timedelta

import pytest

from src.extensions import db
from src.models import (
    Attendance,
    AuditLog,
    Course,
    Department,
    Enrollment,
    Section,
    Student,
    User,
)
from tests.conftest import TEST_PASSWORD

CLASS_DATE = "2026-10-12"


def login(client, email, password=TEST_PASSWORD):
    """Log in through the authentication API."""
    return client.post("/api/auth/login", json={"email": email, "password": password})


@pytest.fixture
def course_setup(app, make_user):
    """A course taught by faculty1, with 3 enrolled students and 1 student not enrolled."""
    make_user("faculty", email="faculty1@pes.edu")
    make_user("faculty", email="faculty2@pes.edu")
    with app.app_context():
        faculty = User.query.filter_by(email="faculty1@pes.edu").one()
        department = Department(name="CSE-AIML")
        db.session.add(department)
        db.session.flush()
        section = Section(name="H", department_id=department.id)
        db.session.add(section)
        db.session.flush()
        course = Course(
            code="UE24AM241A",
            name="Software Engineering",
            credits=4,
            department_id=department.id,
            faculty_id=faculty.id,
        )
        students = [
            Student(
                srn=f"PES1UG24AM{index:03d}",
                name=f"Student {index}",
                email=f"student{index}@pes.edu",
                semester=4,
                department_id=department.id,
                section_id=section.id,
            )
            for index in range(1, 5)
        ]
        db.session.add(course)
        db.session.add_all(students)
        db.session.flush()
        for student in students[:3]:
            db.session.add(Enrollment(student_id=student.id, course_id=course.id))
        db.session.commit()
        return {
            "course_id": course.id,
            "enrolled": [student.id for student in students[:3]],
            "not_enrolled": students[3].id,
            "faculty_id": faculty.id,
        }


@pytest.fixture
def faculty_client(app, course_setup):  # pylint: disable=unused-argument
    """A client logged in as the course's assigned faculty member."""
    client = app.test_client()
    assert login(client, "faculty1@pes.edu").status_code == 200
    return client


def mark(client, course_id, records, class_date=CLASS_DATE):
    """Save attendance for a class date."""
    return client.put(
        f"/api/faculty/attendance/{course_id}", json={"date": class_date, "records": records}
    )


def test_roster_defaults_to_all_present(faculty_client, course_setup):
    """Before saving, every enrolled student is listed as present (SAD 4.5, NF-002)."""
    response = faculty_client.get(
        f"/api/faculty/attendance/{course_setup['course_id']}?date={CLASS_DATE}"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["recorded"] is False
    assert [row["student_id"] for row in data["students"]] == course_setup["enrolled"]
    assert all(row["present"] for row in data["students"])


def test_tc_att_01_assigned_faculty_marks_and_other_faculty_is_forbidden(
    app, faculty_client, course_setup
):
    """TC-ATT-01: 3 rows saved for the date; a different faculty member gets HTTP 403."""
    course_id = course_setup["course_id"]
    first, second, third = course_setup["enrolled"]
    records = [
        {"student_id": first, "present": True},
        {"student_id": second, "present": False},
        {"student_id": third, "present": True},
    ]
    response = mark(faculty_client, course_id, records)
    assert response.status_code == 200
    assert response.get_json() == {"date": CLASS_DATE, "saved": 3, "corrected": 0}

    with app.app_context():
        rows = Attendance.query.filter_by(course_id=course_id, date=date(2026, 10, 12)).all()
        assert len(rows) == 3
        assert {row.student_id: row.present for row in rows} == {
            first: True,
            second: False,
            third: True,
        }

    other = app.test_client()
    login(other, "faculty2@pes.edu")
    assert mark(other, course_id, records).status_code == 403
    assert other.get(f"/api/faculty/attendance/{course_id}?date={CLASS_DATE}").status_code == 403


def test_tc_att_02_correction_updates_value_and_writes_audit_row(app, faculty_client, course_setup):
    """TC-ATT-02: changing absent -> present updates the row and creates an audit-log row."""
    course_id = course_setup["course_id"]
    student_id = course_setup["enrolled"][0]
    mark(faculty_client, course_id, [{"student_id": student_id, "present": False}])

    response = mark(faculty_client, course_id, [{"student_id": student_id, "present": True}])
    assert response.status_code == 200
    assert response.get_json()["corrected"] == 1

    reopened = faculty_client.get(f"/api/faculty/attendance/{course_id}?date={CLASS_DATE}")
    assert reopened.get_json()["recorded"] is True
    row = next(r for r in reopened.get_json()["students"] if r["student_id"] == student_id)
    assert row["present"] is True

    with app.app_context():
        audits = AuditLog.query.filter_by(entity="attendance").all()
        assert len(audits) == 1
        assert audits[0].user_id == course_setup["faculty_id"]
        assert audits[0].action == "attendance changed"
        assert (audits[0].old_value, audits[0].new_value) == ("absent", "present")
        assert audits[0].timestamp is not None


def test_saving_same_values_again_creates_no_audit_rows(app, faculty_client, course_setup):
    """Re-saving unchanged attendance is not a correction."""
    course_id = course_setup["course_id"]
    records = [{"student_id": sid, "present": True} for sid in course_setup["enrolled"]]
    mark(faculty_client, course_id, records)
    response = mark(faculty_client, course_id, records)
    assert response.get_json()["corrected"] == 0
    with app.app_context():
        assert AuditLog.query.count() == 0
        assert Attendance.query.count() == 3


@pytest.mark.parametrize("role", ["admin", "student"])
def test_only_faculty_can_use_attendance_api(client, make_user, course_setup, role):
    """Admin and Student get HTTP 403 on /api/faculty/attendance (SR-002)."""
    make_user(role)
    login(client, f"{role}@pes.edu")
    course_id = course_setup["course_id"]
    assert client.get(f"/api/faculty/attendance/{course_id}?date={CLASS_DATE}").status_code == 403
    assert mark(client, course_id, [{"student_id": 1, "present": True}]).status_code == 403


def test_student_not_enrolled_is_rejected_and_nothing_saved(app, faculty_client, course_setup):
    """A record for a student outside the course fails the whole save."""
    records = [
        {"student_id": course_setup["enrolled"][0], "present": True},
        {"student_id": course_setup["not_enrolled"], "present": True},
    ]
    response = mark(faculty_client, course_setup["course_id"], records)
    assert response.status_code == 400
    assert "not enrolled" in response.get_json()["error"]
    with app.app_context():
        assert Attendance.query.count() == 0


@pytest.mark.parametrize(
    "class_date",
    ["", "12-10-2026", "2026-02-30", (date.today() + timedelta(days=1)).isoformat(), None],
)
def test_invalid_or_future_dates_are_rejected(faculty_client, course_setup, class_date):
    """Dates are validated on the server (SR-007)."""
    student_id = course_setup["enrolled"][0]
    response = mark(
        faculty_client,
        course_setup["course_id"],
        [{"student_id": student_id, "present": True}],
        class_date=class_date,
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "records",
    [
        [],
        "all",
        [{"student_id": "1", "present": True}],
        [{"present": True}],
        ["x"],
    ],
)
def test_invalid_records_are_rejected(faculty_client, course_setup, records):
    """Malformed records get HTTP 400."""
    assert mark(faculty_client, course_setup["course_id"], records).status_code == 400


def test_invalid_present_value_and_duplicates_are_rejected(faculty_client, course_setup):
    """present must be a boolean, and a student may appear only once."""
    course_id = course_setup["course_id"]
    student_id = course_setup["enrolled"][0]
    assert (
        mark(faculty_client, course_id, [{"student_id": student_id, "present": "yes"}]).status_code
        == 400
    )
    duplicate = [
        {"student_id": student_id, "present": True},
        {"student_id": student_id, "present": False},
    ]
    assert mark(faculty_client, course_id, duplicate).status_code == 400


def test_non_object_body_and_missing_course(faculty_client, course_setup):
    """A non-JSON-object body is a 400; an unknown course is a 404."""
    url = f"/api/faculty/attendance/{course_setup['course_id']}"
    assert faculty_client.put(url, json=["not", "an", "object"]).status_code == 400
    assert faculty_client.get(f"/api/faculty/attendance/9999?date={CLASS_DATE}").status_code == 404
    assert mark(faculty_client, 9999, [{"student_id": 1, "present": True}]).status_code == 404
