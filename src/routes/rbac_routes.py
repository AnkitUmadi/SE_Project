"""Role navigation menus API (Issue #5).

Feature endpoints are protected with the decorators in src/rbac.py
(e.g. @admin_required) inside each feature's own blueprint.
"""

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from src.rbac import ROLE_MENUS

rbac_bp = Blueprint("rbac", __name__)


@rbac_bp.get("/api/auth/menus")
@login_required
def get_role_menus():
    """Return only the navigation menu items allowed for the current session role."""
    items = ROLE_MENUS.get(current_user.role, [])
    return jsonify({"role": current_user.role, "menus": items})
