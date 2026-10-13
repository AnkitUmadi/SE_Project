"""Role-protected API routes for RBAC verification and role navigation menus (Issue #5)."""

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from src.rbac import (
    ROLE_MENUS,
    admin_required,
    faculty_required,
    staff_required,
    student_required,
)

rbac_bp = Blueprint("rbac", __name__)


@rbac_bp.get("/api/auth/menus")
@login_required
def get_role_menus():
    """Return only the navigation menu items allowed for the current session role."""
    items = ROLE_MENUS.get(current_user.role, [])
    return jsonify({"role": current_user.role, "menus": items})


@rbac_bp.route("/api/admin/students", methods=["GET", "POST"])
@admin_required
def admin_students():
    """Admin-only student management endpoint (SRS-F-002, TC-AUTH-03)."""
    return jsonify({"role": current_user.role, "students": []})


@rbac_bp.route("/api/admin/fees", methods=["GET", "PUT"])
@admin_required
def admin_fees():
    """Admin-only fee status management endpoint (SRS-F-015, TC-SEC-02)."""
    return jsonify({"role": current_user.role, "fees": []})


@rbac_bp.get("/api/admin/audit-log")
@admin_required
def admin_audit_log():
    """Admin-only audit log endpoint (SRS-F-025, TC-SEC-02)."""
    return jsonify({"role": current_user.role, "audit_log": []})


@rbac_bp.get("/api/faculty/courses")
@faculty_required
def faculty_courses():
    """Faculty-only assigned courses endpoint (SRS-F-011, TC-SEC-02)."""
    return jsonify({"role": current_user.role, "courses": []})


@rbac_bp.route("/api/marks/<int:course_id>/<int:student_id>", methods=["GET", "POST", "PUT"])
@faculty_required
def faculty_marks(course_id, student_id):
    """Faculty-only marks entry endpoint (SRS-F-002, TC-AUTH-03, TC-SEC-02)."""
    return jsonify(
        {
            "role": current_user.role,
            "course_id": course_id,
            "student_id": student_id,
        }
    )


@rbac_bp.get("/api/staff/students")
@staff_required
def staff_student_directory():
    """Admin and Faculty student directory endpoint (SRS-F-007, TC-SEC-02)."""
    return jsonify({"role": current_user.role, "students": []})


@rbac_bp.get("/api/student/attendance")
@student_required
def student_attendance():
    """Student-only own attendance endpoint (SRS-F-021, TC-SEC-02)."""
    return jsonify({"role": current_user.role, "attendance": []})


@rbac_bp.get("/api/results/me")
@student_required
def student_own_results():
    """Student-only own results endpoint (SRS-F-021, TC-SEC-02)."""
    return jsonify({"role": current_user.role, "courses": [], "sgpa": 0.0})
