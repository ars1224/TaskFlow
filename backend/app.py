import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from sqlalchemy import text
from sqlalchemy.engine import URL
from auth import auth_bp
from main import main_bp
from profile_routes import profile_bp
from datetime import timedelta

from extensions import csrf, db, login_manager

load_dotenv()


def create_app():
    app = Flask(__name__)

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "taskflow-development-key",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=7)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access that page."
    login_manager.login_message_category = "warning"

    # Load the application routes
    from auth import auth_bp
    from main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp)
        

    @app.get("/api/health")
    def health():
        return jsonify(
            status="success",
            message="TaskFlow is running",
        )

    @app.get("/api/database-health")
    def database_health():
        try:
            db.session.execute(text("SELECT 1"))

            return jsonify(
                status="success",
                message="TaskFlow successfully connected to PostgreSQL",
            )
        except Exception as error:
            return jsonify(
                status="error",
                message=str(error),
            ), 500

    # Creates tables that do not exist during development
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)