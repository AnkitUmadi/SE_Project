"""Login / logout API (AuthModule in the SAD). All routes are under /api/auth."""

from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.csrf import generate_csrf

from src.services.auth_service import AuthError, authenticate

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/csrf")
def csrf_token():
    """Give React a CSRF token. It must send it back in the X-CSRFToken header on every POST."""
    return jsonify({"csrf_token": generate_csrf()})


@auth_bp.post("/login")
def login():
    """Log in with email + password. 200 on success, 401 wrong details, 423 locked."""
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        user = authenticate(email, password)
    except AuthError as error:
        return jsonify({"error": error.message}), error.status_code

    login_user(user)
    session.permanent = True  # expires after 30 minutes without activity (F-003)
    return jsonify({"user": user.to_dict()})


@auth_bp.post("/logout")
@login_required
def logout():
    """End the session."""
    logout_user()
    return jsonify({"message": "Logged out."})


@auth_bp.get("/me")
def me():
    """Who is logged in right now? React calls this when the page loads."""
    if not current_user.is_authenticated:
        return jsonify({"error": "Not logged in."}), 401
    return jsonify({"user": current_user.to_dict()})
