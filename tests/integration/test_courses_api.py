"""Integration tests for courses, syllabus and enrollment (Issues #11, #12)."""

import pytest

from src.extensions import db
from src.models import Department, Enrollment, Section, Student, User
from tests.conftest import TEST_PASSWORD


def login(client, email, password=TEST_PASSWORD):
    """Log in through the authentication API."""
    return client.post("/api/auth/login", json={"email": email, "password": password})


def user_id(app, email):
    """Database id of the user with this email."""
    with app.app_context():
        return User.query.filter_by(email=email).one().id


@pytest.fixture
def admin_client(client, make_user):
    """A client logged in as Admin."""
    make_user("admin")
    assert login(client, "admin@pes.edu").status_code == 200
    return client


@pytest.fixture
def faculty_id(app, make_user):
    """Id of a Faculty user who can be assigned to courses."""
    make_user("faculty", email="faculty1@pes.edu")
    return user_id(app, "faculty1@pes.edu")


@pytest.fixture
def department_id(app):
    """A department with one section."""
    with app.app_context():
        department = Department(name="CSE-AIML")
        db.session.add(department)
        db.session.flush()
        db.session.add(Section(name="H", department_id=department.id))
        db.session.commit()
        return department.id


@pytest.fixture
def student_ids(app, department_id):
    """Three students in the department's section."""
    with app.app_context():
        section = Section.query.filter_by(department_id=department_id).first()
        students = [
            Student(
                srn=f"PES1UG24AM{index:03d}",
                name=f"Student {index}",
                email=f"student{index}@pes.edu",
                semester=4,
                department_id=department_id,
                section_id=section.id,
            )
            for index in range(1, 4)
        ]
        db.session.add_all(students)
        db.session.commit()
        return [student.id for student in students]


def course_payload(dept_id, **overrides):
    """A valid course payload."""
    payload = {
        "code": "UE24AM241A",
        "name": "Software Engineering",
        "credits": 4,
        "department_id": dept_id,
        "syllabus": "Unit 1: Requirements. Unit 2: Design.",
    }
    payload.update(overrides)
    return payload


def create_course(client, dept_id, **overrides):
    """Create a course and return the response."""
    return client.post("/api/admin/courses", json=course_payload(dept_id, **overrides))


# ---------------------------------------------------------------- access control


def test_unauthenticated_user_cannot_list_courses(client):
    """Not logged in -> HTTP 401."""
    assert client.get("/api/admin/courses").status_code == 401


@pytest.mark.parametrize("role", ["faculty", "student"])
def test_non_admin_cannot_manage_courses(client, make_user, role):
    """Faculty and Students get HTTP 403 on the admin course API (SR-002)."""
    make_user(role)
    assert login(client, f"{role}@pes.edu").status_code == 200

    assert client.get("/api/admin/courses").status_code == 403
    assert client.post("/api/admin/courses", json={}).status_code == 403
    assert client.post("/api/admin/courses/1/enrollments", json={}).status_code == 403


# ---------------------------------------------------------------- TC-CRS-01


def test_tc_crs_01_create_course_and_reject_duplicate_code(admin_client, department_id, faculty_id):
    """TC-CRS-01: first course saved and listed; same code again is rejected."""
    response = create_course(admin_client, department_id, faculty_id=faculty_id)
    assert response.status_code == 201
    course = response.get_json()["course"]
    assert course["code"] == "UE24AM241A"
    assert course["faculty_name"] == "Test faculty"
    assert course["department_name"] == "CSE-AIML"

    listed = admin_client.get("/api/admin/courses").get_json()["courses"]
    assert [item["code"] for item in listed] == ["UE24AM241A"]

    duplicate = create_course(admin_client, department_id, code="ue24am241a", name="Copy")
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.get_json()["error"]
    assert len(admin_client.get("/api/admin/courses").get_json()["courses"]) == 1


def test_admin_can_edit_and_delete_course(admin_client, department_id):
    """Edits persist; a deleted course is no longer listed."""
    course_id = create_course(admin_client, department_id).get_json()["course"]["id"]

    response = admin_client.put(f"/api/admin/courses/{course_id}", json={"credits": 3})
    assert response.status_code == 200
    assert response.get_json()["course"]["credits"] == 3
    assert response.get_json()["course"]["name"] == "Software Engineering"

    assert admin_client.delete(f"/api/admin/courses/{course_id}").status_code == 200
    assert admin_client.get("/api/admin/courses").get_json()["courses"] == []
    assert admin_client.delete(f"/api/admin/courses/{course_id}").status_code == 404


def test_update_cannot_take_another_courses_code(admin_client, department_id):
    """Editing a course to an existing code is rejected."""
    create_course(admin_client, department_id)
    second = create_course(admin_client, department_id, code="UE24AM242A", name="ML")
    second_id = second.get_json()["course"]["id"]

    response = admin_client.put(f"/api/admin/courses/{second_id}", json={"code": "UE24AM241A"})
    assert response.status_code == 409


def test_search_courses_by_code_or_name(admin_client, department_id):
    """?search= matches on course code or name."""
    create_course(admin_client, department_id)
    create_course(admin_client, department_id, code="UE24AM242A", name="Machine Learning")

    by_name = admin_client.get("/api/admin/courses?search=machine").get_json()["courses"]
    assert [course["code"] for course in by_name] == ["UE24AM242A"]
    by_code = admin_client.get("/api/admin/courses?search=241").get_json()["courses"]
    assert [course["code"] for course in by_code] == ["UE24AM241A"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"code": ""},
        {"name": "   "},
        {"credits": 0},
        {"credits": 7},
        {"credits": True},
        {"credits": "4"},
        {"department_id": "x"},
        {"syllabus": 42},
    ],
)
def test_invalid_course_fields_are_rejected(admin_client, department_id, overrides):
    """Invalid values are rejected on the server with HTTP 400 (SR-007)."""
    assert create_course(admin_client, department_id, **overrides).status_code == 400


def test_unknown_department_or_faculty_is_rejected(app, admin_client, department_id, make_user):
    """Department and faculty must exist; a Student user cannot be a course's faculty."""
    assert create_course(admin_client, 9999).status_code == 404
    assert create_course(admin_client, department_id, faculty_id=9999).status_code == 404

    make_user("student")
    student_user_id = user_id(app, "student@pes.edu")
    assert create_course(admin_client, department_id, faculty_id=student_user_id).status_code == 404


def test_faculty_dropdown_lists_only_faculty(
    admin_client, faculty_id, make_user
):  # pylint: disable=unused-argument
    """GET /api/admin/faculty returns Faculty users only."""
    make_user("student")
    response = admin_client.get("/api/admin/faculty")
    assert response.status_code == 200
    assert [user["email"] for user in response.get_json()["faculty"]] == ["faculty1@pes.edu"]


def test_missing_course_returns_404(admin_client):
    """Unknown course ids return HTTP 404."""
    assert admin_client.get("/api/admin/courses/9999").status_code == 404
    assert admin_client.put("/api/admin/courses/9999", json={"name": "X"}).status_code == 404
    assert admin_client.get("/api/admin/courses/9999/enrollments").status_code == 404


# ---------------------------------------------------------------- TC-CRS-02


def test_tc_crs_02_saved_syllabus_is_shown_to_enrolled_student(
    app, admin_client, department_id, student_ids, make_user
):
    """TC-CRS-02: syllabus saved by Admin is displayed when the Student opens the course."""
    course_id = create_course(admin_client, department_id).get_json()["course"]["id"]
    response = admin_client.put(
        f"/api/admin/courses/{course_id}", json={"syllabus": "Unit 1: SRS. Unit 2: SAD."}
    )
    assert response.status_code == 200
    assert admin_client.get(f"/api/admin/courses/{course_id}").get_json()["course"]["syllabus"] == (
        "Unit 1: SRS. Unit 2: SAD."
    )

    make_user("student", email="student1@pes.edu")
    with app.app_context():
        student = db.session.get(Student, student_ids[0])
        student.user_id = User.query.filter_by(email="student1@pes.edu").one().id
        db.session.add(Enrollment(student_id=student.id, course_id=course_id))
        db.session.commit()

    student_client = app.test_client()
    assert login(student_client, "student1@pes.edu").status_code == 200
    courses = student_client.get("/api/student/courses").get_json()["courses"]
    assert len(courses) == 1
    assert courses[0]["syllabus"] == "Unit 1: SRS. Unit 2: SAD."


def test_student_without_profile_sees_no_courses(client, make_user):
    """A Student login with no linked student record gets an empty list."""
    make_user("student")
    login(client, "student@pes.edu")
    assert client.get("/api/student/courses").get_json() == {"courses": []}


def test_assigned_faculty_can_edit_syllabus(
    app, admin_client, department_id, faculty_id, make_user
):
    """Assigned faculty sees and edits the syllabus; another faculty member gets 403."""
    course_id = create_course(admin_client, department_id, faculty_id=faculty_id).get_json()[
        "course"
    ]["id"]
    make_user("faculty", email="faculty2@pes.edu")

    faculty_client = app.test_client()
    login(faculty_client, "faculty1@pes.edu")
    mine = faculty_client.get("/api/faculty/courses").get_json()["courses"]
    assert [course["id"] for course in mine] == [course_id]

    url = f"/api/faculty/courses/{course_id}/syllabus"
    response = faculty_client.put(url, json={"syllabus": "Updated syllabus"})
    assert response.status_code == 200
    assert response.get_json()["course"]["syllabus"] == "Updated syllabus"
    assert faculty_client.put(url, json={"syllabus": 5}).status_code == 400

    other_client = app.test_client()
    login(other_client, "faculty2@pes.edu")
    assert other_client.get("/api/faculty/courses").get_json()["courses"] == []
    assert other_client.put(url, json={"syllabus": "Hacked"}).status_code == 403


# ---------------------------------------------------------------- TC-CRS-03


def test_tc_crs_03_enroll_student_and_reject_duplicate(admin_client, department_id, student_ids):
    """TC-CRS-03: enrolled student appears in the roster; enrolling again is rejected."""
    course_id = create_course(admin_client, department_id).get_json()["course"]["id"]
    url = f"/api/admin/courses/{course_id}/enrollments"

    response = admin_client.post(url, json={"student_ids": [student_ids[0]]})
    assert response.status_code == 201
    roster = admin_client.get(url).get_json()["students"]
    assert [student["id"] for student in roster] == [student_ids[0]]

    duplicate = admin_client.post(url, json={"student_ids": [student_ids[0]]})
    assert duplicate.status_code == 409
    assert "already enrolled" in duplicate.get_json()["error"]
    assert len(admin_client.get(url).get_json()["students"]) == 1


def test_enrolling_several_students_is_all_or_nothing(admin_client, department_id, student_ids):
    """If one student in the batch is already enrolled, none of the batch is saved (NF-005)."""
    course_id = create_course(admin_client, department_id).get_json()["course"]["id"]
    url = f"/api/admin/courses/{course_id}/enrollments"
    admin_client.post(url, json={"student_ids": [student_ids[1]]})

    response = admin_client.post(url, json={"student_ids": [student_ids[0], student_ids[1]]})
    assert response.status_code == 409
    roster = admin_client.get(url).get_json()["students"]
    assert [student["id"] for student in roster] == [student_ids[1]]

    response = admin_client.post(url, json={"student_ids": [student_ids[0], student_ids[2]]})
    assert response.status_code == 201
    assert len(admin_client.get(url).get_json()["students"]) == 3


def test_remove_student_from_course(admin_client, department_id, student_ids):
    """A removed student leaves the roster; removing again returns 404."""
    course_id = create_course(admin_client, department_id).get_json()["course"]["id"]
    url = f"/api/admin/courses/{course_id}/enrollments"
    admin_client.post(url, json={"student_ids": [student_ids[0]]})

    assert admin_client.delete(f"{url}/{student_ids[0]}").status_code == 200
    assert admin_client.get(url).get_json()["students"] == []
    assert admin_client.delete(f"{url}/{student_ids[0]}").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"student_ids": []},
        {"student_ids": "1"},
        {"student_ids": [True]},
        {"student_ids": [1, 1]},
    ],
)
def test_invalid_enrollment_payload_is_rejected(admin_client, department_id, payload):
    """Bad enrollment requests get HTTP 400."""
    course_id = create_course(admin_client, department_id).get_json()["course"]["id"]
    response = admin_client.post(f"/api/admin/courses/{course_id}/enrollments", json=payload)
    assert response.status_code == 400


def test_enrolling_unknown_student_returns_404(admin_client, department_id):
    """A student id that does not exist cannot be enrolled."""
    course_id = create_course(admin_client, department_id).get_json()["course"]["id"]
    response = admin_client.post(
        f"/api/admin/courses/{course_id}/enrollments", json={"student_ids": [9999]}
    )
    assert response.status_code == 404
