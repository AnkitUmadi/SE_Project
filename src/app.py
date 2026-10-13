"""Application factory: builds and configures the Flask app."""

from flask import Flask, jsonify
from flask_wtf.csrf import CSRFError

from src import models  # pylint: disable=unused-import  # registers all tables
from src.config import Config
from src.extensions import csrf, db, login_manager
from src.routes.auth import auth_bp
from src.routes.health import health_bp
from src.routes.departments import departments_bp


def create_app(config_class=Config):
    """Create the Flask app with the given settings class."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(departments_bp)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


def register_error_handlers(app):
    """Return JSON errors (not HTML pages) so React can show a clear message."""

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "Please log in first."}), 401

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return jsonify({"error": f"Security token missing or expired: {error.description}"}), 400
