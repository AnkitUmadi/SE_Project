"""Admin API for managing departments and sections."""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from src.extensions import db
from src.models.department import Department
from src.models.section import Section

departments_bp = Blueprint(
    "departments",
    __name__,
    url_prefix="/api/departments",
)


def admin_required():
    """Return a JSON 403 response unless the current user is an Admin."""
    if not current_user.is_authenticated or current_user.role != "admin":
        return jsonify({"error": "Admin access required."}), 403
    return None


@departments_bp.before_request
@login_required
def require_login():
    """Require a logged-in user for every department API endpoint."""
    return None


@departments_bp.get("")
def list_departments():
    """List departments and their sections."""
    denied = admin_required()
    if denied:
        return denied

    departments = Department.query.order_by(Department.name).all()
    return jsonify(
        {
            "departments": [
                {
                    **department.to_dict(),
                    "sections": [section.to_dict() for section in department.sections],
                }
                for department in departments
            ]
        }
    )


@departments_bp.post("")
def create_department():
    """Create a department."""
    denied = admin_required()
    if denied:
        return denied

    data = request.get_json(silent=True) or {}
    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Department name is required."}), 400

    name = name.strip()
    if Department.query.filter_by(name=name).first():
        return jsonify({"error": "Department already exists."}), 409

    department = Department(name=name)
    db.session.add(department)
    db.session.commit()
    return jsonify({"department": department.to_dict()}), 201


@departments_bp.put("/<int:department_id>")
def update_department(department_id):
    """Update a department name."""
    denied = admin_required()
    if denied:
        return denied

    department = db.session.get(Department, department_id)
    if department is None:
        return jsonify({"error": "Department not found."}), 404

    data = request.get_json(silent=True) or {}
    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Department name is required."}), 400

    name = name.strip()
    duplicate = Department.query.filter(
        Department.name == name,
        Department.id != department_id,
    ).first()
    if duplicate:
        return jsonify({"error": "Department already exists."}), 409

    department.name = name
    db.session.commit()
    return jsonify({"department": department.to_dict()})


@departments_bp.delete("/<int:department_id>")
def delete_department(department_id):
    """Delete a department and its sections."""
    denied = admin_required()
    if denied:
        return denied

    department = db.session.get(Department, department_id)
    if department is None:
        return jsonify({"error": "Department not found."}), 404

    db.session.delete(department)
    db.session.commit()
    return jsonify({"message": "Department deleted."})


@departments_bp.post("/<int:department_id>/sections")
def create_section(department_id):
    """Create a section inside a department."""
    denied = admin_required()
    if denied:
        return denied

    department = db.session.get(Department, department_id)
    if department is None:
        return jsonify({"error": "Department not found."}), 404

    data = request.get_json(silent=True) or {}
    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Section name is required."}), 400

    name = name.strip()
    existing = Section.query.filter_by(
        name=name,
        department_id=department_id,
    ).first()
    if existing:
        return jsonify({"error": "Section already exists in this department."}), 409

    section = Section(name=name, department_id=department_id)
    db.session.add(section)
    db.session.commit()
    return jsonify({"section": section.to_dict()}), 201


# pylint: disable=too-many-return-statements
@departments_bp.put("/sections/<int:section_id>")
def update_section(section_id):
    """Update a section name or move it to another department."""
    denied = admin_required()
    if denied:
        return denied

    section = db.session.get(Section, section_id)
    if section is None:
        return jsonify({"error": "Section not found."}), 404

    data = request.get_json(silent=True) or {}
    name = data.get("name", section.name)
    department_id = data.get("department_id", section.department_id)

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Section name is required."}), 400

    if not isinstance(department_id, int) or isinstance(department_id, bool):
        return jsonify({"error": "A valid department_id is required."}), 400

    if db.session.get(Department, department_id) is None:
        return jsonify({"error": "Department not found."}), 404

    name = name.strip()
    duplicate = (
        Section.query.filter_by(
            name=name,
            department_id=department_id,
        )
        .filter(Section.id != section_id)
        .first()
    )
    if duplicate:
        return jsonify({"error": "Section already exists in this department."}), 409

    section.name = name
    section.department_id = department_id
    db.session.commit()
    return jsonify({"section": section.to_dict()})


@departments_bp.delete("/sections/<int:section_id>")
def delete_section(section_id):
    """Delete a section."""
    denied = admin_required()
    if denied:
        return denied

    section = db.session.get(Section, section_id)
    if section is None:
        return jsonify({"error": "Section not found."}), 404

    db.session.delete(section)
    db.session.commit()
    return jsonify({"message": "Section deleted."})
