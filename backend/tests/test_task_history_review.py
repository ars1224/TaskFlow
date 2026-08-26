from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from extensions import db
from models import Task


NZ_TIMEZONE = ZoneInfo(
    "Pacific/Auckland"
)


def test_finished_past_task_appears_in_history(
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

    completed_time = datetime.combine(
        yesterday,
        datetime.min.time(),
        tzinfo=NZ_TIMEZONE,
    )

    with app.app_context():
        task = Task(
            title="TEST - Finished History",
            scheduled_date=(
                today
                + timedelta(days=5)
            ),
            due_date=(
                today
                + timedelta(days=7)
            ),
            status="completed",
            priority="medium",
            completed_at=completed_time,
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    response = login_user_a.get(
        "/tasks/history"
    )

    assert response.status_code == 200

    html = response.get_data(
        as_text=True
    )

    assert (
        f'id="taskDetailsModal{task_id}"'
        in html
    )


def test_active_past_task_does_not_appear_in_history(
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

    with app.app_context():
        task = Task(
            title="TEST - Active Carry Over",
            scheduled_date=yesterday,
            due_date=yesterday,
            status="on-going",
            priority="high",
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    history_response = login_user_a.get(
        "/tasks/history"
    )

    assert (
        history_response.status_code
        == 200
    )

    history_html = (
        history_response.get_data(
            as_text=True
        )
    )

    # Active carry-over task must not
    # exist as a History task card/modal.
    assert (
        f'id="taskDetailsModal{task_id}"'
        not in history_html
    )

    task_list_response = login_user_a.get(
        "/tasks/"
    )

    assert (
        task_list_response.status_code
        == 200
    )

    task_list_html = (
        task_list_response.get_data(
            as_text=True
        )
    )

    # It must still exist on Task List.
    assert (
        f'data-bs-target="#taskDetailsModal{task_id}"'
        in task_list_html
    )


def test_review_saves_remarks_and_reflection(
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

    with app.app_context():
        task = Task(
            title=(
                "TEST - Review Persistence"
            ),
            scheduled_date=yesterday,
            due_date=today,
            status="completed",
            priority="low",
            completed_at=(
                datetime.now(
                    NZ_TIMEZONE
                )
                - timedelta(days=1)
            ),
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    response = login_user_a.post(
        f"/tasks/{task_id}/review",
        data={
            "status": "completed",
            "priority": "high",
            "remarks": (
                "Testing saved remarks."
            ),
            "reflection": (
                "Testing saved reflection."
            ),
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
        assert task.status == "completed"
        assert task.priority == "high"

        assert (
            task.remarks
            == "Testing saved remarks."
        )

        assert (
            task.reflection
            == "Testing saved reflection."
        )

        assert task.completed_at is not None


def test_review_finished_task_back_to_ongoing(
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

    with app.app_context():
        task = Task(
            title=(
                "TEST - Reopen Finished Task"
            ),
            scheduled_date=yesterday,
            due_date=yesterday,
            status="completed",
            priority="medium",
            completed_at=(
                datetime.now(
                    NZ_TIMEZONE
                )
                - timedelta(days=1)
            ),
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    response = login_user_a.post(
        f"/tasks/{task_id}/review",
        data={
            "status": "on-going",
            "priority": "medium",
            "remarks": "Needs more work.",
            "reflection": "",
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
        assert task.status == "on-going"
        assert task.completed_at is None
        assert (
            task.remarks
            == "Needs more work."
        )

    history_response = login_user_a.get(
        "/tasks/history"
    )

    history_html = (
        history_response.get_data(
            as_text=True
        )
    )

    # Reopened task must leave History.
    assert (
        f'id="taskDetailsModal{task_id}"'
        not in history_html
    )

    task_list_response = login_user_a.get(
        "/tasks/"
    )

    task_list_html = (
        task_list_response.get_data(
            as_text=True
        )
    )

    # Reopened task must return
    # to Task List.
    assert (
        f'data-bs-target="#taskDetailsModal{task_id}"'
        in task_list_html
    )