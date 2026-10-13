"""Integration tests for Role-Based Access Control on API routes (Issue #5).

Covers:
- TC-AUTH-03: Logged in as Student, call admin and marks routes directly -> HTTP 403;
  menus endpoint returns only Student items.
- TC-SEC-02: For each role (Admin, Faculty, Student), request every route that role must not access
  -> All return HTTP 403.
- SRS-SR-002: Role is always read from the server session, never trusted from client query/body data.
"""

import pytest

from src.app import create_app
from src.config import TestConfig
from src.extensions import db
from tests.conftest import TEST_PASSWORD
from tests.rbac_probe import probe_bp


@pytest.fixture
def app():
    """App with the test-only RBAC probe routes added (see tests/rbac_probe.py)."""
    application = create_app(TestConfig)
    application.register_blueprint(probe_bp)
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


def login(client, email, password=TEST_PASSWORD):
    """Helper: call the login API."""
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_unauthenticated_requests_to_protected_routes_return_401(client):
    protected_gets = [
        "/api/auth/menus",
        "/api/admin/rbac-probe/students",
        "/api/admin/rbac-probe/fees",
        "/api/admin/rbac-probe/audit-log",
        "/api/faculty/rbac-probe/courses",
        "/api/staff/rbac-probe/students",
        "/api/student/rbac-probe/attendance",
        "/api/results/me/rbac-probe",
    ]
    for path in protected_gets:
        res = client.get(path)
        assert res.status_code == 401, f"Expected 401 for unauthenticated GET {path}"

    res_post = client.post("/api/marks/rbac-probe/1/1", json={"marks_obtained": 40})
    assert res_post.status_code == 401


def test_tc_auth_03_student_calling_admin_and_marks_gets_403_and_sees_student_menus(
    client, make_user
):
    """TC-AUTH-03: Logged in as Student, admin and marks routes return HTTP 403."""
    make_user("student", email="s1@pes.edu")
    login(client, "s1@pes.edu")

    admin_res = client.get("/api/admin/rbac-probe/students")
    assert admin_res.status_code == 403
    assert "Forbidden" in admin_res.get_json()["error"]

    marks_get = client.get("/api/marks/rbac-probe/101/1")
    assert marks_get.status_code == 403

    marks_post = client.post("/api/marks/rbac-probe/101/1", json={"marks_obtained": 50})
    assert marks_post.status_code == 403

    menus_res = client.get("/api/auth/menus")
    assert menus_res.status_code == 200
    body = menus_res.get_json()
    assert body["role"] == "student"
    paths = [m["path"] for m in body["menus"]]
    assert all(p.startswith("/student") for p in paths)


def test_tc_sec_02_every_role_denied_on_routes_it_must_not_access(client, make_user):
    """TC-SEC-02: For each role, request every route that role must not access -> All return 403."""
    make_user("admin", email="admin@pes.edu")
    make_user("faculty", email="faculty@pes.edu")
    make_user("student", email="student@pes.edu")

    # 1. Student denied on Admin, Faculty, Marks, and Staff routes; allowed on Student routes
    login(client, "student@pes.edu")
    for forbidden_get in (
        "/api/admin/rbac-probe/students",
        "/api/admin/rbac-probe/fees",
        "/api/admin/rbac-probe/audit-log",
        "/api/faculty/rbac-probe/courses",
        "/api/marks/rbac-probe/1/1",
        "/api/staff/rbac-probe/students",
    ):
        assert client.get(forbidden_get).status_code == 403
    assert client.post("/api/admin/rbac-probe/students", json={}).status_code == 403
    assert client.put("/api/admin/rbac-probe/fees", json={}).status_code == 403
    assert client.post("/api/marks/rbac-probe/1/1", json={}).status_code == 403
    assert client.get("/api/student/rbac-probe/attendance").status_code == 200
    assert client.get("/api/results/me/rbac-probe").status_code == 200
    client.post("/api/auth/logout")

    # 2. Faculty denied on Admin and Student routes; allowed on Faculty, Marks, and Staff routes
    login(client, "faculty@pes.edu")
    for forbidden_get in (
        "/api/admin/rbac-probe/students",
        "/api/admin/rbac-probe/fees",
        "/api/admin/rbac-probe/audit-log",
        "/api/student/rbac-probe/attendance",
        "/api/results/me/rbac-probe",
    ):
        assert client.get(forbidden_get).status_code == 403
    assert client.post("/api/admin/rbac-probe/students", json={}).status_code == 403
    assert client.put("/api/admin/rbac-probe/fees", json={}).status_code == 403
    assert client.get("/api/faculty/rbac-probe/courses").status_code == 200
    assert client.get("/api/marks/rbac-probe/101/7").status_code == 200
    assert client.post("/api/marks/rbac-probe/101/7", json={"marks": 45}).status_code == 200
    assert client.get("/api/staff/rbac-probe/students").status_code == 200
    assert client.get("/api/auth/menus").get_json()["role"] == "faculty"
    client.post("/api/auth/logout")

    # 3. Admin denied on Faculty-only (marks/courses) and Student-only routes; allowed on Admin & Staff
    login(client, "admin@pes.edu")
    for forbidden_get in (
        "/api/faculty/rbac-probe/courses",
        "/api/marks/rbac-probe/101/7",
        "/api/student/rbac-probe/attendance",
        "/api/results/me/rbac-probe",
    ):
        assert client.get(forbidden_get).status_code == 403
    assert client.post("/api/marks/rbac-probe/101/7", json={"marks": 45}).status_code == 403
    assert client.get("/api/admin/rbac-probe/students").status_code == 200
    assert (
        client.post("/api/admin/rbac-probe/students", json={"srn": "PES1UG23CS001"}).status_code
        == 200
    )
    assert client.get("/api/admin/rbac-probe/fees").status_code == 200
    assert client.put("/api/admin/rbac-probe/fees", json={"fee_paid": True}).status_code == 200
    assert client.get("/api/admin/rbac-probe/audit-log").status_code == 200
    assert client.get("/api/staff/rbac-probe/students").status_code == 200
    assert client.get("/api/auth/menus").get_json()["role"] == "admin"


def test_srs_sr_002_client_cannot_spoof_role_via_query_or_body(client, make_user):
    """SRS-SR-002: Role is always read from the server session, never from request parameters."""
    make_user("student", email="spoof@pes.edu")
    login(client, "spoof@pes.edu")

    res = client.post(
        "/api/admin/rbac-probe/students?role=admin",
        json={"role": "admin"},
        headers={"X-Role": "admin"},
    )
    assert res.status_code == 403
