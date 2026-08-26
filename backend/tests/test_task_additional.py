from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from extensions import db
from models import Task


NZ_TIMEZONE = ZoneInfo(
    "Pacific/Auckland"
)


def test_view_task_details_are_rendered(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    with app.app_context():
        task = Task(
            title="TEST - View Details",
            description="Detailed task description.",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="high",
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    response = login_user_a.get(
        "/tasks/"
    )

    assert response.status_code == 200

    html = response.get_data(
        as_text=True
    )

    assert (
        f'id="taskDetailsModal{task_id}"'
        in html
    )

    assert "TEST - View Details" in html
    assert "Detailed task description." in html
    assert "High" in html


def test_edit_task_persists_changes(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    tomorrow = (
        today
        + timedelta(days=1)
    )

    with app.app_context():
        task = Task(
            title="TEST - Before Edit",
            description="Before edit.",
            scheduled_date=today,
            due_date=tomorrow,
            status="on-going",
            priority="low",
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    response = login_user_a.post(
        f"/tasks/{task_id}/edit",
        data={
            "title": "TEST - After Edit",
            "description": "After edit.",
            "priority": "high",
            "scheduled_date": today.isoformat(),
            "due_date": tomorrow.isoformat(),
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        task = db.session.get(
            Task,
            task_id,
        )

        assert task is not None

        assert (
            task.title
            == "TEST - After Edit"
        )

        assert (
            task.description
            == "After edit."
        )

        assert task.priority == "high"
        assert task.scheduled_date == today
        assert task.due_date == tomorrow
        assert task.status == "on-going"


def test_finished_future_task_can_return_to_incomplete(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    future = (
        today
        + timedelta(days=7)
    )

    with app.app_context():
        task = Task(
            title="TEST - Undo Finished",
            scheduled_date=future,
            due_date=future,
            status="completed",
            priority="medium",
            completed_at=datetime.now(
                NZ_TIMEZONE
            ),
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

        assert task is not None

        # Future task returns to Yet-to-do.
        assert task.status == "yet-to-do"

        assert task.completed_at is None


def test_dropped_task_cannot_be_completed(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    with app.app_context():
        task = Task(
            title="TEST - Dropped Locked",
            scheduled_date=today,
            due_date=today,
            status="dropped",
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

        assert task is not None
        assert task.status == "dropped"
        assert task.completed_at is None


def test_history_search_filters_records(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    yesterday = (
        today
        - timedelta(days=1)
    )

    completed_at = (
        datetime.now(
            NZ_TIMEZONE
        )
        - timedelta(days=1)
    )

    with app.app_context():
        alpha = Task(
            title="TEST - History Alpha",
            scheduled_date=yesterday,
            due_date=yesterday,
            status="completed",
            priority="medium",
            completed_at=completed_at,
            user_id=users["user_a_id"],
        )

        beta = Task(
            title="TEST - History Beta",
            scheduled_date=yesterday,
            due_date=yesterday,
            status="completed",
            priority="medium",
            completed_at=completed_at,
            user_id=users["user_a_id"],
        )

        db.session.add_all(
            [
                alpha,
                beta,
            ]
        )

        db.session.commit()

        alpha_id = alpha.id
        beta_id = beta.id

    response = login_user_a.get(
        "/tasks/history",
        query_string={
            "q": "Alpha",
        },
    )

    assert response.status_code == 200

    html = response.get_data(
        as_text=True
    )

    assert (
        f'id="taskDetailsModal{alpha_id}"'
        in html
    )

    assert (
        f'id="taskDetailsModal{beta_id}"'
        not in html
    )


def test_multiple_priority_filters_work_together(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    with app.app_context():
        high = Task(
            title="TEST - Multi High",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="high",
            user_id=users["user_a_id"],
        )

        medium = Task(
            title="TEST - Multi Medium",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        low = Task(
            title="TEST - Multi Low",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="low",
            user_id=users["user_a_id"],
        )

        db.session.add_all(
            [
                high,
                medium,
                low,
            ]
        )

        db.session.commit()

        high_id = high.id
        medium_id = medium.id
        low_id = low.id

    response = login_user_a.get(
        "/tasks/?priority=high&priority=medium"
    )

    assert response.status_code == 200

    html = response.get_data(
        as_text=True
    )

    assert (
        f'data-bs-target="#taskDetailsModal{high_id}"'
        in html
    )

    assert (
        f'data-bs-target="#taskDetailsModal{medium_id}"'
        in html
    )

    assert (
        f'data-bs-target="#taskDetailsModal{low_id}"'
        not in html
    )