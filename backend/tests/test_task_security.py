from datetime import datetime
from zoneinfo import ZoneInfo

from extensions import db
from models import Task


NZ_TIMEZONE = ZoneInfo("Pacific/Auckland")


def test_user_cannot_see_another_users_task(
    app,
    login_user_b,
    user_a_task,
):
    """
    User B must not see User A's task
    anywhere on User B's Task List.
    """

    response = login_user_b.get(
        "/tasks/",
        follow_redirects=True,
    )

    assert response.status_code == 200

    assert (
        b"TEST - User A Private Task"
        not in response.data
    )


def test_user_cannot_edit_another_users_task(
    app,
    login_user_b,
    user_a_task,
):
    """
    User B must receive 404 when attempting
    to edit a task owned by User A.
    """

    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    response = login_user_b.post(
        f"/tasks/{user_a_task}/edit",
        data={
            "title": "Hacked Task",
            "description": "Unauthorized edit",
            "priority": "low",
            "scheduled_date": (
                today.isoformat()
            ),
            "due_date": (
                today.isoformat()
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code == 404

    # Confirm the task was not changed.
    with app.app_context():
        task = db.session.get(
            Task,
            user_a_task,
        )

        assert task is not None
        assert (
            task.title
            == "TEST - User A Private Task"
        )

        assert task.priority == "high"


def test_user_cannot_drop_another_users_task(
    app,
    login_user_b,
    user_a_task,
):
    """
    User B must not be able to drop
    User A's task.
    """

    response = login_user_b.post(
        f"/tasks/{user_a_task}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 404

    # Task must still be active.
    with app.app_context():
        task = db.session.get(
            Task,
            user_a_task,
        )

        assert task is not None
        assert task.status == "on-going"


def test_user_cannot_complete_another_users_task(
    app,
    login_user_b,
    user_a_task,
):
    """
    User B must not be able to mark
    User A's task as finished.
    """

    response = login_user_b.post(
        f"/tasks/{user_a_task}/toggle-complete",
        follow_redirects=False,
    )

    assert response.status_code == 404

    with app.app_context():
        task = db.session.get(
            Task,
            user_a_task,
        )

        assert task is not None
        assert task.status == "on-going"
        assert task.completed_at is None


def test_user_cannot_review_another_users_task(
    app,
    login_user_b,
    user_a_task,
):
    """
    User B must not be able to change
    User A's review information.
    """

    response = login_user_b.post(
        f"/tasks/{user_a_task}/review",
        data={
            "status": "completed",
            "priority": "low",
            "remarks": "Unauthorized remark",
            "reflection": (
                "Unauthorized reflection"
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code == 404

    with app.app_context():
        task = db.session.get(
            Task,
            user_a_task,
        )

        assert task is not None

        assert task.status == "on-going"
        assert task.priority == "high"
        assert task.remarks is None
        assert task.reflection is None