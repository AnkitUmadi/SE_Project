"""Integration tests for database models, seed script and transaction rollback (TC-REL-01)."""

from datetime import date
import pytest

from src.extensions import db
from src.models import (
    Attendance,
    AuditLog,
    Course,
    Department,
    Marks,
    Section,
    Student,
    User,
)
from src.services.seed_service import (
    DEFAULT_SEED_PASSWORD,
    atomic_transaction,
    seed_database,
    update_marks_with_audit,
)
from scripts.seed import main as run_seed_cli


def test_seed_data_allows_role_logins_via_api(app, client):
    """Seeded Admin, Faculty and Student accounts can log in through /api/auth/login."""
    with app.app_context():
        summary = seed_database()
        assert summary["admins"] == 1
        assert summary["faculty"] == 3
        assert summary["students"] == 30

    for email, expected_role in [
        ("admin@pes.edu", "admin"),
        ("faculty1@pes.edu", "faculty"),
        ("student01@pes.edu", "student"),
    ]:
        res = client.post(
            "/api/auth/login",
            json={"email": email, "password": DEFAULT_SEED_PASSWORD},
        )
        assert res.status_code == 200
        assert res.get_json()["user"]["role"] == expected_role
        client.post("/api/auth/logout")


def test_seed_cli_main_runs_cleanly(monkeypatch, capsys, app):
    """The CLI entrypoint scripts/seed.py seeds the database and prints a summary."""
    monkeypatch.setattr("scripts.seed.create_app", lambda: app)
    run_seed_cli()
    captured = capsys.readouterr().out
    assert "Database seeded successfully:" in captured
    assert "students: 30" in captured


def test_tc_rel_01_integration_marks_and_audit_atomic_rollback(app):
    """TC-REL-01 (SRS-NF-005): Error after marks update before audit insert rolls back."""
    with app.app_context():
        seed_database()
        faculty = User.query.filter_by(email="faculty1@pes.edu").one()
        student = Student.query.filter_by(srn="PES1UG24AM001").one()
        course = Course.query.filter_by(code="UE24AM241A").one()

        marks = Marks(
            student_id=student.id,
            course_id=course.id,
            isa1=14.0,
            isa2=15.0,
            assessment=9.0,
            esa=40.0,
            total=78.0,
            grade="B",
            grade_point=8,
        )
        db.session.add(marks)
        db.session.commit()

        # First verify a normal atomic update succeeds and writes an audit row
        update_marks_with_audit(marks, user_id=faculty.id, updates={"isa1": 16.0})
        assert db.session.get(Marks, marks.id).isa1 == 16.0
        assert db.session.get(Marks, marks.id).total == 80.0
        assert AuditLog.query.count() == 1

        # Now force an error after the marks update but before the audit insert (TC-REL-01)
        def force_error():
            raise RuntimeError("Forced failure before audit log insert")

        with pytest.raises(RuntimeError, match="Forced failure before audit log insert"):
            update_marks_with_audit(
                marks,
                user_id=faculty.id,
                updates={"isa1": 20.0, "esa": 49.0},
                before_audit_hook=force_error,
            )

        db.session.expire_all()
        unchanged = db.session.get(Marks, marks.id)
        assert unchanged.isa1 == 16.0
        assert unchanged.esa == 40.0
        assert unchanged.total == 80.0
        assert AuditLog.query.count() == 1


def test_tc_rel_01_attendance_batch_rollback_on_mid_save_error(app):
    """SRS-NF-005: Simulated failure mid-attendance-save leaves no partial rows."""
    with app.app_context():
        dept = Department(name="ECE")
        db.session.add(dept)
        db.session.flush()
        sec = Section(name="A", department_id=dept.id)
        db.session.add(sec)
        db.session.flush()
        course = Course(code="UE24EC201A", name="Signals", credits=4, department_id=dept.id)
        s1 = Student(
            srn="PES1UG24EC001",
            name="S1",
            email="ec1@pes.edu",
            semester=4,
            section_id=sec.id,
        )
        db.session.add_all([course, s1])
        db.session.commit()

        initial_count = Attendance.query.filter_by(course_id=course.id).count()
        with pytest.raises(ValueError, match="Simulated mid-batch error"):
            with atomic_transaction():
                db.session.add(
                    Attendance(
                        course_id=course.id,
                        student_id=s1.id,
                        date=date(2026, 9, 1),
                        present=True,
                    )
                )
                db.session.flush()
                raise ValueError("Simulated mid-batch error")

        assert Attendance.query.filter_by(course_id=course.id).count() == initial_count
