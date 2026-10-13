"""Test-only "probe" routes for checking RBAC (Issue #5).

They live under the same protected URL prefixes as real features, but use a
special "rbac-probe" path, so they can never clash with real endpoints.
They are registered only in tests, never in the real app.
"""

from flask import Blueprint, jsonify
from flask_login import current_user

from src.rbac import admin_required, faculty_required, staff_required, student_required

probe_bp = Blueprint("rbac_probe", __name__, url_prefix="/api")
METHODS = ["GET", "POST", "PUT"]


def _answer(name):
    return jsonify({"role": current_user.role, "probe": name})


@probe_bp.route("/admin/rbac-probe/<path:name>", methods=METHODS)
@admin_required
def admin_probe(name):
    """Admin-only probe."""
    return _answer(name)


@probe_bp.route("/faculty/rbac-probe/<path:name>", methods=METHODS)
@faculty_required
def faculty_probe(name):
    """Faculty-only probe."""
    return _answer(name)


@probe_bp.route("/marks/rbac-probe/<path:name>", methods=METHODS)
@faculty_required
def marks_probe(name):
    """Faculty-only marks probe."""
    return _answer(name)


@probe_bp.route("/staff/rbac-probe/<path:name>", methods=METHODS)
@staff_required
def staff_probe(name):
    """Admin + Faculty probe."""
    return _answer(name)


@probe_bp.route("/student/rbac-probe/<path:name>", methods=METHODS)
@student_required
def student_probe(name):
    """Student-only probe."""
    return _answer(name)


@probe_bp.route("/results/me/rbac-probe", methods=METHODS)
@student_required
def results_probe():
    """Student-only own-results probe."""
    return _answer("results")
