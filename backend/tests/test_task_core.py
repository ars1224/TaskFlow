from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from extensions import db
from models import Task


NZ_TIMEZONE = ZoneInfo(
    "Pacific/Auckland"
)


def test_create_task(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    response = login_user_a.post(
        "/tasks/create",
        data={
            "title": "TEST - Create Task",
            "description": "Created by pytest.",
            "priority": "high",
            "scheduled_date": today.isoformat(),
            "due_date": today.isoformat(),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        task = db.session.scalar(
            db.select(Task).where(
                Task.title == "TEST - Create Task"
            )
        )

        assert task is not None
        assert task.status == "on-going"
        assert task.priority == "high"
        assert task.user_id == users["user_a_id"]


def test_search_tasks(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    with app.app_context():
        task_one = Task(
            title="TEST - Search Alpha",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        task_two = Task(
            title="TEST - Search Beta",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        db.session.add_all(
            [
                task_one,
                task_two,
            ]
        )

        db.session.commit()

        alpha_id = task_one.id
        beta_id = task_two.id


    response = login_user_a.get(
        "/tasks/?q=Alpha",
        follow_redirects=True,
    )

    assert response.status_code == 200

    html = response.get_data(
        as_text=True
    )


    # Alpha must appear as an actual Task List card.
    assert (
        f'data-bs-target="#taskDetailsModal{alpha_id}"'
        in html
    )


    # Beta may still appear elsewhere, such as the
    # notification dropdown, but it must NOT appear
    # as a Task List card.
    assert (
        f'data-bs-target="#taskDetailsModal{beta_id}"'
        not in html
    )

def test_complete_task(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    with app.app_context():
        task = Task(
            title="TEST - Complete Task",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    response = login_user_a.post(
        f"/tasks/{task_id}/toggle-complete",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        task = db.session.get(
            Task,
            task_id,
        )

        assert task.status == "completed"
        assert task.completed_at is not None


def test_drop_task(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    with app.app_context():
        task = Task(
            title="TEST - Drop Task",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="low",
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    response = login_user_a.post(
        f"/tasks/{task_id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        task = db.session.get(
            Task,
            task_id,
        )

        assert task is not None
        assert task.status == "dropped"


def test_future_task_completed_early_counts_today(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    future_date = (
        today
        + timedelta(days=10)
    )

    with app.app_context():
        task = Task(
            title="TEST - Early Completion",
            scheduled_date=future_date,
            due_date=future_date,
            status="yet-to-do",
            priority="high",
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    # Finish the future task early.
    response = login_user_a.post(
        f"/tasks/{task_id}/toggle-complete",
        follow_redirects=False,
    )

    assert response.status_code == 302

    # It should now count on today's Dashboard.
    response = login_user_a.get(
        "/dashboard",
        follow_redirects=True,
    )

    assert response.status_code == 200

    assert (
        b"TEST - Early Completion"
        in response.data
    )

    assert (
        b"1 of 1"
        in response.data
    )

    with app.app_context():
        task = db.session.get(
            Task,
            task_id,
        )

        assert task.status == "completed"
        assert task.completed_at is not None

        # Original future plan is preserved.
        assert task.scheduled_date == future_date