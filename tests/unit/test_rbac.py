"""Unit tests for RBAC helpers and decorators (Issue #5: SRS-F-002, SRS-SR-002)."""

import pytest

from src.models.user import Role
from src.rbac import (
    ROLE_MENUS,
    admin_required,
    check_required_roles_for_path,
    faculty_required,
    roles_required,
    staff_required,
    student_required,
)


def test_roles_required_rejects_empty_or_invalid_role():
    with pytest.raises(ValueError, match="roles_required expects roles"):
        roles_required()

    with pytest.raises(ValueError, match="roles_required expects roles"):
        roles_required("superadmin")


def test_check_required_roles_for_path_matches_prefixes():
    assert check_required_roles_for_path("/api/admin") == (Role.ADMIN,)
    assert check_required_roles_for_path("/api/admin/students") == (Role.ADMIN,)
    assert check_required_roles_for_path("/api/faculty/courses") == (Role.FACULTY,)
    assert check_required_roles_for_path("/api/marks/101/42") == (Role.FACULTY,)
    assert check_required_roles_for_path("/api/student/attendance") == (Role.STUDENT,)
    assert check_required_roles_for_path("/api/esa/register") == (Role.STUDENT,)
    assert check_required_roles_for_path("/api/esa/drop") == (Role.STUDENT,)
    assert check_required_roles_for_path("/api/results/me") == (Role.STUDENT,)


def test_check_required_roles_for_path_ignores_unmatched_or_partial_prefix():
    assert check_required_roles_for_path("/api/health") is None
    assert check_required_roles_for_path("/api/auth/login") is None
    assert check_required_roles_for_path("/api/administrator") is None


def test_role_menus_defined_for_all_roles():
    assert set(ROLE_MENUS.keys()) == set(Role.ALL)
    for role in Role.ALL:
        items = ROLE_MENUS[role]
        assert len(items) > 0
        for item in items:
            assert "label" in item and "path" in item
            assert item["path"].startswith(f"/{role}")


def test_convenience_decorators_are_callable():
    for dec in (admin_required, faculty_required, student_required, staff_required):
        wrapped = dec(lambda: ("ok", 200))
        assert callable(wrapped)
