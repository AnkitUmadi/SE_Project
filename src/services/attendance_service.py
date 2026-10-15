"""Attendance marking and correction rules (AttendanceService in the SAD; SRS-F-011, F-012).

Every save is one database transaction (SRS-NF-005): the attendance rows and the
audit-log rows for any corrections are written together or not at all.
"""

from datetime import date

from src.extensions import db
from src.models import Attendance, AuditLog, Enrollment
from src.services.course_service import course_roster
from src.services.seed_service import atomic_transaction


class AttendanceError(Exception):
    """An attendance problem, with the HTTP status code the API should return."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def parse_class_date(value, today=None):
    """Turn 'YYYY-MM-DD' into a date. Future dates are rejected (SRS-SR-007).

    `today` can be passed in by tests.
    """
    if not isinstance(value, str):
        raise AttendanceError("Date is required (YYYY-MM-DD).")
    try:
        class_date = date.fromisoformat(value.strip())
    except ValueError as error:
        raise AttendanceError("Date must be a valid date in YYYY-MM-DD format.") from error
    if class_date > (today or date.today()):
        raise AttendanceError("Attendance cannot be marked for a future date.")
    return class_date


def check_assigned_faculty(course, user):
    """Only the faculty member assigned to the course may mark its attendance."""
    if course.faculty_id != user.id:
        raise AttendanceError("Only the faculty assigned to this course can mark attendance.", 403)


def class_attendance(course, class_date):
    """Every enrolled student with their attendance for that date.

    Students without a saved entry are shown as present ('All present' default, SAD 4.5).
    """
    saved = {
        row.student_id: row
        for row in Attendance.query.filter_by(course_id=course.id, date=class_date).all()
    }
    students = [
        {
            "student_id": student.id,
            "srn": student.srn,
            "name": student.name,
            "present": saved[student.id].present if student.id in saved else True,
        }
        for student in course_roster(course)
    ]
    return {"recorded": bool(saved), "students": students}


def _validate_records(course, records):
    """Return {student_id: present}; every student must be enrolled in the course."""
    if not isinstance(records, list) or not records:
        raise AttendanceError("records must be a non-empty list.")

    enrolled = {row.student_id for row in Enrollment.query.filter_by(course_id=course.id).all()}
    cleaned = {}
    for record in records:
        if not isinstance(record, dict):
            raise AttendanceError("Each record needs a student_id and present (true/false).")
        student_id = record.get("student_id")
        present = record.get("present")
        if not isinstance(student_id, int) or isinstance(student_id, bool):
            raise AttendanceError("Each record needs a valid student_id.")
        if not isinstance(present, bool):
            raise AttendanceError("present must be true or false.")
        if student_id not in enrolled:
            raise AttendanceError(f"Student {student_id} is not enrolled in {course.code}.")
        if student_id in cleaned:
            raise AttendanceError(f"Student {student_id} is listed more than once.")
        cleaned[student_id] = present
    return cleaned


def _label(present):
    return "present" if present else "absent"


def save_attendance(course, user, class_date, records, before_commit_hook=None):
    """Create or correct attendance for one class date.

    New entries are inserted. A changed entry is a correction (SRS-F-012) and gets an
    audit-log row with the old and new value. `before_commit_hook` lets tests force an
    error mid-save to prove nothing partial is kept (TC-REL-01).
    Returns (saved_count, corrected_count).
    """
    check_assigned_faculty(course, user)
    cleaned = _validate_records(course, records)

    existing = {
        row.student_id: row
        for row in Attendance.query.filter_by(course_id=course.id, date=class_date).all()
    }
    corrected = 0
    with atomic_transaction():
        for student_id, present in cleaned.items():
            row = existing.get(student_id)
            if row is None:
                db.session.add(
                    Attendance(
                        course_id=course.id,
                        student_id=student_id,
                        date=class_date,
                        present=present,
                    )
                )
                continue
            if row.present == present:
                continue
            db.session.add(
                AuditLog(
                    user_id=user.id,
                    action="attendance changed",
                    entity="attendance",
                    entity_id=str(row.id),
                    old_value=_label(row.present),
                    new_value=_label(present),
                )
            )
            row.present = present
            corrected += 1
        db.session.flush()
        if before_commit_hook is not None:
            before_commit_hook()
    return len(cleaned), corrected
