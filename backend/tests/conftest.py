import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


# -------------------------------------------------
# Make the backend folder importable during tests
# -------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIR),
    )


# These imports must come AFTER sys.path is updated.
from app import create_app
from extensions import db
from models import Task, User


NZ_TIMEZONE = ZoneInfo(
    "Pacific/Auckland"
)


@pytest.fixture()
def app(tmp_path):
    """
    Create an isolated TaskFlow app for each test.

    The test database is temporary SQLite and does
    not touch the real PostgreSQL database.
    """

    database_file = (
        tmp_path
        / "taskflow_test.db"
    )

    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,

            "SECRET_KEY": (
                "taskflow-test-secret-key"
            ),

            "SQLALCHEMY_DATABASE_URI": (
                "sqlite:///"
                + database_file.as_posix()
            ),

            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def users(app):
    with app.app_context():

        user_a = User(
            full_name="Test User A",
            email="usera@test.com",
        )

        user_a.set_password(
            "Password123!"
        )


        user_b = User(
            full_name="Test User B",
            email="userb@test.com",
        )

        user_b.set_password(
            "Password123!"
        )


        db.session.add_all(
            [
                user_a,
                user_b,
            ]
        )

        db.session.commit()


        user_a_id = user_a.id
        user_b_id = user_b.id


    return {
        "user_a_id": user_a_id,
        "user_b_id": user_b_id,

        "user_a_email": (
            "usera@test.com"
        ),

        "user_b_email": (
            "userb@test.com"
        ),

        "password": (
            "Password123!"
        ),
    }


@pytest.fixture()
def user_a_task(
    app,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()


    with app.app_context():

        task = Task(
            title=(
                "TEST - User A Private Task"
            ),

            description=(
                "This task belongs only "
                "to User A."
            ),

            scheduled_date=today,
            due_date=today,

            status="on-going",
            priority="high",

            user_id=(
                users["user_a_id"]
            ),
        )


        db.session.add(task)
        db.session.commit()

        task_id = task.id


    return task_id



@pytest.fixture()
def login_user_b(
    client,
    users,
):
    response = client.post(
        "/auth/login",
        data={
            "email": users["user_b_email"],
            "password": users["password"],
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    return client


@pytest.fixture()
def login_user_a(
    client,
    users,
):
    response = client.post(
        "/auth/login",
        data={
            "email": users["user_a_email"],
            "password": users["password"],
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    return client