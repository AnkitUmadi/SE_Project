"""Unit tests for SAD 3.6 database models, seed data and atomic transactions (Issue #4)."""

from datetime import date
import pytest
from sqlalchemy.exc import IntegrityError

from src.extensions import db
from src.models import (
    Attendance,
    AuditLog,
    Course,
    Department,
    EligibilityOverride,
    Enrollment,
    ExamRegistration,
    ExamWindow,
    FeeState,
    FeeStatus,
    Marks,
    Role,
    Section,
    Student,
)
from src.services.auth_service import authenticate, create_user
from src.services.seed_service import (
    DEFAULT_SEED_PASSWORD,
    seed_database,
    update_marks_with_audit,
)
from tests.conftest import TEST_PASSWORD

EXPECTED_TABLES = {
    "users",
    "departments",
    "sections",
    "students",
    "courses",
    "enrollments",
    "attendance",
    "fee_status",
    "exam_window",
    "exam_registrations",
    "eligibility_overrides",
    "marks",
    "audit_log",
}


def test_all_sad_3_6_tables_are_registered(app):
    """Every table listed in SAD Section 3.6 exists in SQLAlchemy metadata."""
    with app.app_context():
        assert EXPECTED_TABLES.issubset(set(db.metadata.tables.keys()))


def test_models_roundtrip_and_to_dict_serialization(app):
    """All models save cleanly and serialize expected fields via to_dict()."""
    with app.app_context():
        admin = create_user("admin1@pes.edu", "Test admin", TEST_PASSWORD, "admin")
        faculty = create_user("fac1@pes.edu", "Test faculty", TEST_PASSWORD, "faculty")
        student_user = create_user("stu1@pes.edu", "Test student", TEST_PASSWORD, "student")

        dept = Department(name="CSE-AIML")
        db.session.add(dept)
        db.session.flush()
        assert dept.to_dict() == {"id": dept.id, "name": "CSE-AIML"}

        sec = Section(name="H", department_id=dept.id)
        db.session.add(sec)
        db.session.flush()
        assert sec.to_dict()["department_name"] == "CSE-AIML"

        student = Student(
            srn="PES1UG24AM999",
            name="Test Student",
            email="stu1@pes.edu",
            semester=4,
            section_id=sec.id,
            user_id=student_user.id,
        )
        db.session.add(student)
        db.session.flush()
        stu_dict = student.to_dict()
        assert stu_dict["srn"] == "PES1UG24AM999"
        assert stu_dict["department_id"] == dept.id
        assert stu_dict["department_name"] == "CSE-AIML"
        assert stu_dict["section_name"] == "H"

        course = Course(
            code="UE24AM241A",
            name="Software Engineering",
            credits=4,
            department_id=dept.id,
            faculty_id=faculty.id,
            syllabus="Unit 1: SRS",
        )
        db.session.add(course)
        db.session.flush()
        assert course.to_dict()["code"] == "UE24AM241A"
        assert course.to_dict()["faculty_name"] == "Test faculty"

        enrollment = Enrollment(student_id=student.id, course_id=course.id)
        att = Attendance(
            course_id=course.id,
            student_id=student.id,
            date=date(2026, 8, 10),
            present=True,
        )
        fee = FeeStatus(student_id=student.id, semester=4, status=FeeState.PAID)
        window = ExamWindow(is_open=True)
        reg = ExamRegistration(student_id=student.id, course_id=course.id)
        override = EligibilityOverride(
            student_id=student.id,
            course_id=course.id,
            reason="Medical certificate approved",
            admin_id=admin.id,
        )
        marks = Marks(
            student_id=student.id,
            course_id=course.id,
            isa1=18.0,
            isa2=17.0,
            assessment=9.0,
            esa=40.0,
            total=84.0,
            grade="A",
            grade_point=9,
        )
        audit = AuditLog(
            user_id=faculty.id,
            action="marks entered",
            entity="marks",
            entity_id="1",
            old_value=None,
            new_value="84.0",
        )
        db.session.add_all([enrollment, att, fee, window, reg, override, marks, audit])
        db.session.commit()

        assert enrollment.to_dict()["student_id"] == student.id
        assert att.to_dict()["date"] == "2026-08-10"
        assert fee.to_dict()["status"] == FeeState.PAID
        assert window.to_dict()["is_open"] is True
        assert reg.to_dict()["course_id"] == course.id
        assert override.to_dict()["reason"] == "Medical certificate approved"
        assert marks.to_dict()["total"] == 84.0
        assert audit.to_dict()["user_email"] == "fac1@pes.edu"


def test_unique_constraints_reject_duplicates(app):
    """Duplicate SRN, course code, enrollment, or same-date attendance raise IntegrityError."""
    with app.app_context():
        dept = Department(name="CSE")
        db.session.add(dept)
        db.session.flush()
        sec = Section(name="A", department_id=dept.id)
        db.session.add(sec)
        db.session.flush()

        s1 = Student(
            srn="PES1UG24CS001",
            name="Alice",
            email="alice@pes.edu",
            semester=4,
            section_id=sec.id,
        )
        db.session.add(s1)
        db.session.commit()

        # Duplicate SRN
        db.session.add(
            Student(
                srn="PES1UG24CS001",
                name="Bob",
                email="bob@pes.edu",
                semester=4,
                section_id=sec.id,
            )
        )
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Duplicate enrollment pair
        course = Course(code="UE24CS241A", name="OS", credits=4, department_id=dept.id)
        db.session.add(course)
        db.session.commit()

        db.session.add(Enrollment(student_id=s1.id, course_id=course.id))
        db.session.commit()

        db.session.add(Enrollment(student_id=s1.id, course_id=course.id))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_seed_database_creates_expected_counts_and_is_idempotent(app):
    """Seed script creates 1 admin, 3 faculty, 30 students, 2 depts, 3 sections, 5 courses."""
    with app.app_context():
        summary_first = seed_database()
        assert summary_first["admins"] == 1
        assert summary_first["faculty"] == 3
        assert summary_first["students"] == 30
        assert summary_first["departments"] == 2
        assert summary_first["sections"] == 3
        assert summary_first["courses"] == 5
        assert summary_first["fee_status"] == 30
        assert summary_first["enrollments"] == 80  # 20*3 (AIML) + 10*2 (CSE)
        assert summary_first["attendance"] == 500  # 20*20 + 10*10

        # Re-running seed_database is idempotent (no duplicate rows created)
        summary_second = seed_database()
        assert summary_second == summary_first

        # Verify seeded accounts can authenticate
        admin = authenticate("admin@pes.edu", DEFAULT_SEED_PASSWORD)
        assert admin.role == Role.ADMIN

        # Verify attendance boundary patterns (90%, 75%, 70%) in UE24AM241A
        se_course = Course.query.filter_by(code="UE24AM241A").one()
        for srn, expected_present in [
            ("PES1UG24AM001", 18),  # 90%
            ("PES1UG24AM002", 15),  # 75% boundary
            ("PES1UG24AM003", 14),  # 70% shortage
        ]:
            stu = Student.query.filter_by(srn=srn).one()
            present_count = Attendance.query.filter_by(
                course_id=se_course.id, student_id=stu.id, present=True
            ).count()
            assert present_count == expected_present

        # Verify Student 30 has UNPAID fees and 90% attendance in UE24CS241A
        stu30 = Student.query.filter_by(srn="PES1UG24CS030").one()
        fee30 = FeeStatus.query.filter_by(student_id=stu30.id).one()
        assert fee30.status == FeeState.UNPAID


def test_tc_rel_01_error_before_audit_rolls_back_marks_update(app):
    """TC-REL-01 (SRS-NF-005): Force an error after marks update but before audit insert."""
    with app.app_context():
        faculty = create_user("fac_rel@pes.edu", "Faculty Rel", TEST_PASSWORD, "faculty")
        dept = Department(name="CSE-AIML")
        db.session.add(dept)
        db.session.flush()
        sec = Section(name="H", department_id=dept.id)
        db.session.add(sec)
        db.session.flush()
        student = Student(
            srn="PES1UG24AM100",
            name="Rollback Student",
            email="rollback@pes.edu",
            semester=4,
            section_id=sec.id,
        )
        course = Course(
            code="UE24AM299A",
            name="Reliability Engineering",
            credits=4,
            department_id=dept.id,
            faculty_id=faculty.id,
        )
        db.session.add_all([student, course])
        db.session.flush()

        marks = Marks(
            student_id=student.id,
            course_id=course.id,
            isa1=15.0,
            isa2=16.0,
            assessment=8.0,
            esa=36.0,
            total=75.0,
            grade="B",
            grade_point=8,
        )
        db.session.add(marks)
        db.session.commit()

        def fail_before_audit():
            raise RuntimeError("Simulated database failure before audit insert")

        with pytest.raises(RuntimeError, match="Simulated database failure"):
            update_marks_with_audit(
                marks,
                user_id=faculty.id,
                updates={"isa1": 20.0},
                before_audit_hook=fail_before_audit,
            )

        # Verify transaction was rolled back: marks unchanged and no audit row written
        db.session.expire_all()
        persisted = db.session.get(Marks, marks.id)
        assert persisted.isa1 == 15.0
        assert persisted.total == 75.0
        assert AuditLog.query.count() == 0
