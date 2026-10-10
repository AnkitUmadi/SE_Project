"""Application factory: builds and configures the Flask app."""

from flask import Flask

from src.config import Config
from src.extensions import csrf, db, login_manager
from src.routes.health import health_bp


def create_app(config_class=Config):
    """Create the Flask app with the given settings class."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(health_bp)

    with app.app_context():
        db.create_all()

    return app
