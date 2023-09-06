"""
Main Application package.
"""
from flask import (
    Flask,
)
from application.shared.secrets import secrets
from sqlalchemy.ext.declarative import declarative_base
from application.settings.db_config import init_connection_engine
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker
)
from flask_login import LoginManager


# Database configuration
engine = init_connection_engine()
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

login_manager = LoginManager()


def register_blueprints(app: Flask):
    """
    This function registers flask blueprints to flask application
    """
    from .views import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return None


def create_app() -> Flask:
    """
    this function create Flask Application
    """
    app: Flask = Flask(__name__)
    register_blueprints(app)
    app.config['SECRET_KEY'] = secrets['secret_key']
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    login_manager.init_app(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()
    return app
