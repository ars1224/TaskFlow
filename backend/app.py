import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from sqlalchemy import text
from sqlalchemy.engine import URL

from extensions import csrf, db, login_manager, migrate
from notifications import get_notifications


load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)

    # -------------------------------------------------
    # NORMAL DATABASE CONFIGURATION
    # -------------------------------------------------

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv(
            "DB_HOST",
            "localhost",
        ),
        port=int(
            os.getenv(
                "DB_PORT",
                "5432",
            )
        ),
        database=os.getenv("DB_NAME"),
    )


    # -------------------------------------------------
    # APPLICATION CONFIGURATION
    # -------------------------------------------------

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "taskflow-development-key",
    )

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = database_url

    app.config[
        "SQLALCHEMY_TRACK_MODIFICATIONS"
    ] = False


    # Session security

    app.config[
        "SESSION_COOKIE_HTTPONLY"
    ] = True

    app.config[
        "SESSION_COOKIE_SAMESITE"
    ] = "Lax"

    app.config[
        "PERMANENT_SESSION_LIFETIME"
    ] = timedelta(
        hours=8
    )


    # Remember-me cookie

    app.config[
        "REMEMBER_COOKIE_HTTPONLY"
    ] = True

    app.config[
        "REMEMBER_COOKIE_SAMESITE"
    ] = "Lax"

    app.config[
        "REMEMBER_COOKIE_DURATION"
    ] = timedelta(
        days=7
    )


    # -------------------------------------------------
    # TEST CONFIGURATION
    #
    # Pytest can replace PostgreSQL with a temporary
    # SQLite database before SQLAlchemy is initialized.
    # -------------------------------------------------

    if test_config is not None:
        app.config.update(
            test_config
        )


    # -------------------------------------------------
    # EXTENSIONS
    # -------------------------------------------------

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    migrate.init_app(
        app,
        db,
    )


    # -------------------------------------------------
    # FLASK-LOGIN
    # -------------------------------------------------

    login_manager.login_view = (
        "auth.login"
    )

    login_manager.login_message = (
        "Please log in to access that page."
    )

    login_manager.login_message_category = (
        "warning"
    )


    # -------------------------------------------------
    # BLUEPRINTS
    # -------------------------------------------------

    from auth import auth_bp
    from main import main_bp
    from profile_routes import profile_bp
    from task_routes import task_bp

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        main_bp
    )

    app.register_blueprint(
        profile_bp
    )

    app.register_blueprint(
        task_bp
    )


    # -------------------------------------------------
    # HEALTH CHECK
    # -------------------------------------------------

    @app.get("/api/health")
    def health():
        return jsonify(
            status="success",
            message="TaskFlow is running",
        )


    # -------------------------------------------------
    # DATABASE HEALTH CHECK
    # -------------------------------------------------

    @app.get("/api/database-health")
    def database_health():
        try:
            db.session.execute(
                text("SELECT 1")
            )

            return jsonify(
                status="success",
                message=(
                    "TaskFlow successfully "
                    "connected to the database"
                ),
            )

        except Exception as error:
            return jsonify(
                status="error",
                message=str(error),
            ), 500


    # -------------------------------------------------
    # GLOBAL NOTIFICATIONS
    # -------------------------------------------------

    @app.context_processor
    def inject_notifications():
        return get_notifications()


    return app


app = create_app()


if __name__ == "__main__":
    debug_enabled = (
        os.environ.get(
            "FLASK_DEBUG",
            "",
        ).lower()
        in {
            "1",
            "true",
            "yes",
        }
    )

    app.run(
        debug=debug_enabled
    )