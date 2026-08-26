from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from extensions import db
from models import Task


NZ_TIMEZONE = ZoneInfo(
    "Pacific/Auckland"
)


def test_create_task_rejects_empty_title(
    app,
    login_user_a,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    response = login_user_a.post(
        "/tasks/create",
        data={
            "title": "",
            "description": "No title",
            "priority": "medium",
            "scheduled_date": today.isoformat(),
            "due_date": today.isoformat(),
        },
        follow_redirects=False,
    )

    assert response.status_code == 400

    with app.app_context():
        task = db.session.scalar(
            db.select(Task).where(
                Task.description == "No title"
            )
        )

        assert task is None


def test_create_task_rejects_past_scheduled_date(
    app,
    login_user_a,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    yesterday = (
        today
        - timedelta(days=1)
    )

    response = login_user_a.post(
        "/tasks/create",
        data={
            "title": "TEST - Past Date",
            "description": "",
            "priority": "medium",
            "scheduled_date": yesterday.isoformat(),
            "due_date": today.isoformat(),
        },
        follow_redirects=False,
    )

    assert response.status_code == 400

    with app.app_context():
        task = db.session.scalar(
            db.select(Task).where(
                Task.title == "TEST - Past Date"
            )
        )

        assert task is None


def test_create_task_rejects_schedule_after_due_date(
    app,
    login_user_a,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    scheduled = (
        today
        + timedelta(days=5)
    )

    due = (
        today
        + timedelta(days=2)
    )

    response = login_user_a.post(
        "/tasks/create",
        data={
            "title": "TEST - Invalid Dates",
            "description": "",
            "priority": "high",
            "scheduled_date": scheduled.isoformat(),
            "due_date": due.isoformat(),
        },
        follow_redirects=False,
    )

    assert response.status_code == 400

    with app.app_context():
        task = db.session.scalar(
            db.select(Task).where(
                Task.title == "TEST - Invalid Dates"
            )
        )

        assert task is None


def test_create_task_rejects_title_over_150_characters(
    app,
    login_user_a,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    response = login_user_a.post(
        "/tasks/create",
        data={
            "title": "A" * 151,
            "description": "",
            "priority": "low",
            "scheduled_date": today.isoformat(),
            "due_date": today.isoformat(),
        },
        follow_redirects=False,
    )

    assert response.status_code == 400


def test_create_task_rejects_description_over_2000_characters(
    app,
    login_user_a,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    response = login_user_a.post(
        "/tasks/create",
        data={
            "title": "TEST - Long Description",
            "description": "A" * 2001,
            "priority": "medium",
            "scheduled_date": today.isoformat(),
            "due_date": today.isoformat(),
        },
        follow_redirects=False,
    )

    assert response.status_code == 400