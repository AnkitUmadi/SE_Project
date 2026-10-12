"""Seed service and transactional helpers for the Student Record System (Issue #4, NF-005)."""

from contextlib import contextmanager
from datetime import date, timedelta
import os

from werkzeug.security import generate_password_hash

from src.extensions import db
from src.models import (
    Attendance,
    AuditLog,
    Course,
    Department,
    Enrollment,
    ExamWindow,
    FeeState,
    FeeStatus,
    Role,
    Section,
    Student,
    User,
    utc_now,
)

DEFAULT_SEED_PASSWORD = os.getenv("SEED_DEFAULT_PASSWORD", "Password@123")
ACTIVE_SEMESTER = 4

FACULTY_SPECS = [
    ("faculty1@pes.edu", "Dr. Asha Rao"),
    ("faculty2@pes.edu", "Prof. Vivek Kulkarni"),
    ("faculty3@pes.edu", "Dr. Meera Nair"),
]

COURSE_SPECS = [
    (
        "UE24AM241A",
        "Software Engineering",
        4,
        "CSE-AIML",
        "faculty1@pes.edu",
        "Unit 1: Requirements & SRS. Unit 2: Architecture & Design. "
        "Unit 3: Testing & CI/CD. Unit 4: Agile & Project Management.",
    ),
    (
        "UE24AM242A",
        "Machine Learning",
        4,
        "CSE-AIML",
        "faculty2@pes.edu",
        "Unit 1: Supervised Learning. Unit 2: Neural Networks. "
        "Unit 3: Unsupervised Learning. Unit 4: Model Evaluation.",
    ),
    (
        "UE24AM243A",
        "Database Management Systems",
        4,
        "CSE-AIML",
        "faculty1@pes.edu",
        "Unit 1: Relational Model & SQL. Unit 2: Normalization. "
        "Unit 3: Transactions & Concurrency. Unit 4: Indexing.",
    ),
    (
        "UE24CS241A",
        "Operating Systems",
        4,
        "CSE",
        "faculty3@pes.edu",
        "Unit 1: Processes & Threads. Unit 2: CPU Scheduling & Sync. "
        "Unit 3: Memory Management. Unit 4: File Systems.",
    ),
    (
        "UE24CS242A",
        "Computer Networks",
        3,
        "CSE",
        "faculty2@pes.edu",
        "Unit 1: Application & Transport Layers. Unit 2: Network Layer & Routing. "
        "Unit 3: Link Layer & Wireless. Unit 4: Network Security.",
    ),
]


@contextmanager
def atomic_transaction():
    """Execute multi-step database writes as a single atomic transaction (SRS-NF-005).

    If any error occurs before the block completes, all uncommitted changes in the
    session are rolled back so no partial rows are left behind (TC-REL-01).
    """
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def update_marks_with_audit(marks_record, user_id, updates, before_audit_hook=None):
    """Update a Marks record and write an AuditLog entry in one transaction (SRS-NF-005)."""
    with atomic_transaction():
        old_total = marks_record.total
        for field, value in updates.items():
            setattr(marks_record, field, value)
        components = [
            marks_record.isa1 or 0.0,
            marks_record.isa2 or 0.0,
            marks_record.assessment or 0.0,
            marks_record.esa or 0.0,
        ]
        marks_record.total = round(sum(components), 2)
        db.session.flush()

        if before_audit_hook is not None:
            before_audit_hook()

        audit = AuditLog(
            user_id=user_id,
            action="marks changed",
            entity="marks",
            entity_id=str(marks_record.id),
            old_value=str(old_total),
            new_value=str(marks_record.total),
        )
        db.session.add(audit)
    return marks_record


def _get_or_create_user(email, name, role, password_hash):
    """Return existing user by email or create a new one with the precomputed hash."""
    clean_email = email.strip().lower()
    user = User.query.filter_by(email=clean_email).first()
    if user is None:
        user = User(
            email=clean_email,
            name=name.strip(),
            role=role,
            password_hash=password_hash,
        )
        db.session.add(user)
        db.session.flush()
    return user


def _seed_departments_and_sections():
    """Create the 2 departments (CSE-AIML, CSE) and 3 sections (A, H, A)."""
    departments = {}
    for dept_name in ("CSE-AIML", "CSE"):
        dept = Department.query.filter_by(name=dept_name).first()
        if dept is None:
            dept = Department(name=dept_name)
            db.session.add(dept)
            db.session.flush()
        departments[dept_name] = dept

    section_specs = [
        ("CSE-AIML", "A"),
        ("CSE-AIML", "H"),
        ("CSE", "A"),
    ]
    sections = {}
    for dept_name, sec_name in section_specs:
        dept = departments[dept_name]
        sec = Section.query.filter_by(department_id=dept.id, name=sec_name).first()
        if sec is None:
            sec = Section(name=sec_name, department_id=dept.id)
            db.session.add(sec)
            db.session.flush()
        sections[(dept_name, sec_name)] = sec

    return departments, sections


def _seed_students(departments, sections, password_hash):
    """Create 30 students across the 2 departments / 3 sections and their fee status."""
    students = []
    for idx in range(1, 31):
        if idx <= 10:
            dept = departments["CSE-AIML"]
            section = sections[("CSE-AIML", "A")]
            srn = f"PES1UG24AM{idx:03d}"
        elif idx <= 20:
            dept = departments["CSE-AIML"]
            section = sections[("CSE-AIML", "H")]
            srn = f"PES1UG24AM{idx:03d}"
        else:
            dept = departments["CSE"]
            section = sections[("CSE", "A")]
            srn = f"PES1UG24CS{idx:03d}"

        email = f"student{idx:02d}@pes.edu"
        name = f"Student {idx:02d}"
        user = _get_or_create_user(email, name, Role.STUDENT, password_hash)

        student = Student.query.filter_by(srn=srn).first()
        if student is None:
            student = Student(
                srn=srn,
                name=name,
                email=email,
                semester=ACTIVE_SEMESTER,
                department_id=dept.id,
                section_id=section.id,
                user_id=user.id,
            )
            db.session.add(student)
            db.session.flush()
        students.append(student)

        fee = FeeStatus.query.filter_by(student_id=student.id, semester=ACTIVE_SEMESTER).first()
        if fee is None:
            # Student 30 has UNPAID fees for boundary/eligibility testing (STP Section 6)
            status = FeeState.UNPAID if idx == 30 else FeeState.PAID
            db.session.add(
                FeeStatus(student_id=student.id, semester=ACTIVE_SEMESTER, status=status)
            )

    return students


def _seed_courses(departments, faculty_by_email):
    """Create the 5 courses across the 2 departments and assign faculty."""
    courses = {}
    for code, name, credit_hours, dept_name, fac_email, syllabus in COURSE_SPECS:
        course = Course.query.filter_by(code=code).first()
        if course is None:
            course = Course(
                code=code,
                name=name,
                credits=credit_hours,
                department_id=departments[dept_name].id,
                faculty_id=faculty_by_email[fac_email].id,
                syllabus=syllabus,
            )
            db.session.add(course)
            db.session.flush()
        courses[code] = course
    return courses


def _seed_course_attendance(course, students, total_days, present_by_index, default_present):
    """Seed attendance rows for a course over total_days starting 2026-08-01."""
    start_date = date(2026, 8, 1)
    for idx, student in enumerate(students):
        attended = present_by_index.get(idx, default_present)
        for day_offset in range(total_days):
            class_date = start_date + timedelta(days=day_offset)
            exists = Attendance.query.filter_by(
                course_id=course.id, student_id=student.id, date=class_date
            ).first()
            if exists is None:
                db.session.add(
                    Attendance(
                        course_id=course.id,
                        student_id=student.id,
                        date=class_date,
                        present=day_offset < attended,
                    )
                )


def _seed_enrollments_and_attendance(students, courses):
    """Enroll students into their department's courses and seed sample attendance."""
    aiml_students = students[:20]
    cse_students = students[20:]

    aiml_courses = [
        courses["UE24AM241A"],
        courses["UE24AM242A"],
        courses["UE24AM243A"],
    ]
    cse_courses = [courses["UE24CS241A"], courses["UE24CS242A"]]

    for student in aiml_students:
        for course in aiml_courses:
            if (
                Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first()
                is None
            ):
                db.session.add(Enrollment(student_id=student.id, course_id=course.id))

    for student in cse_students:
        for course in cse_courses:
            if (
                Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first()
                is None
            ):
                db.session.add(Enrollment(student_id=student.id, course_id=course.id))

    # UE24AM241A (20 classes): S1=18/20 (90%), S2=15/20 (75%), S3=14/20 (70%), others=17/20 (85%)
    _seed_course_attendance(
        courses["UE24AM241A"],
        aiml_students,
        total_days=20,
        present_by_index={0: 18, 1: 15, 2: 14},
        default_present=17,
    )
    # UE24CS241A (10 classes): Student 30 (unpaid fees)=9/10 (90%), others=8/10 (80%)
    _seed_course_attendance(
        courses["UE24CS241A"],
        cse_students,
        total_days=10,
        present_by_index={len(cse_students) - 1: 9},
        default_present=8,
    )


def seed_database(default_password=None):
    """Populate demo and test data idempotently inside a single transaction.

    Creates:
    - 1 Admin user (admin@pes.edu)
    - 3 Faculty users (faculty1..3@pes.edu)
    - 2 Departments (CSE-AIML, CSE) and 3 Sections (CSE-AIML A & H, CSE A)
    - 30 Students (PES1UG24AM001..020, PES1UG24CS021..030) + fee statuses
    - 5 Courses with syllabi + enrollments + sample attendance + open ExamWindow
    """
    password = default_password or DEFAULT_SEED_PASSWORD
    password_hash = generate_password_hash(password)

    with atomic_transaction():
        _get_or_create_user("admin@pes.edu", "Admin User", Role.ADMIN, password_hash)
        faculty_by_email = {
            email: _get_or_create_user(email, name, Role.FACULTY, password_hash)
            for email, name in FACULTY_SPECS
        }
        departments, sections = _seed_departments_and_sections()
        students = _seed_students(departments, sections, password_hash)
        courses = _seed_courses(departments, faculty_by_email)
        _seed_enrollments_and_attendance(students, courses)

        if ExamWindow.query.first() is None:
            db.session.add(ExamWindow(is_open=True, opened_at=utc_now()))

    return {
        "admins": User.query.filter_by(role=Role.ADMIN).count(),
        "faculty": User.query.filter_by(role=Role.FACULTY).count(),
        "students": Student.query.count(),
        "departments": Department.query.count(),
        "sections": Section.query.count(),
        "courses": Course.query.count(),
        "enrollments": Enrollment.query.count(),
        "attendance": Attendance.query.count(),
        "fee_status": FeeStatus.query.count(),
    }
