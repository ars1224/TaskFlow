import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from extensions import db
from models import Task


NZ_TIMEZONE = ZoneInfo(
    "Pacific/Auckland"
)


def get_status_count(
    html,
    status_class,
):
    pattern = (
        rf'<article class="status-card {status_class}">'
        rf'.*?<strong>\s*(\d+)\s*</strong>'
    )

    match = re.search(
        pattern,
        html,
        re.DOTALL,
    )

    assert match is not None

    return int(
        match.group(1)
    )


def test_dashboard_counts_and_progress(
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

        ongoing = Task(
            title="TEST - Dashboard Ongoing",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        finished = Task(
            title="TEST - Dashboard Finished",
            scheduled_date=today,
            due_date=today,
            status="completed",
            priority="high",
            completed_at=datetime.now(
                NZ_TIMEZONE
            ),
            user_id=users["user_a_id"],
        )

        dropped = Task(
            title="TEST - Dashboard Dropped",
            scheduled_date=today,
            due_date=today,
            status="dropped",
            priority="low",
            user_id=users["user_a_id"],
        )

        overdue = Task(
            title="TEST - Dashboard Overdue",
            scheduled_date=yesterday,
            due_date=yesterday,
            status="on-going",
            priority="high",
            user_id=users["user_a_id"],
        )

        db.session.add_all(
            [
                ongoing,
                finished,
                dropped,
                overdue,
            ]
        )

        db.session.commit()

    response = login_user_a.get(
        "/dashboard"
    )

    assert response.status_code == 200

    html = response.get_data(
        as_text=True
    )

    assert (
        get_status_count(
            html,
            "yet-to-do",
        )
        == 0
    )

    assert (
        get_status_count(
            html,
            "ongoing",
        )
        == 1
    )

    assert (
        get_status_count(
            html,
            "finished",
        )
        == 1
    )

    assert (
        get_status_count(
            html,
            "dropped",
        )
        == 1
    )

    # Dropped tasks are excluded from
    # Daily Progress.
    #
    # Ongoing + Finished = 2 active tasks
    # Finished = 1
    # Progress = 50%
    assert "1 of 2" in html

    assert (
        'aria-valuenow="50"'
        in html
    )

    # Carry-over task should count overdue.
    assert "Overdue:" in html

    assert (
        b"TEST - Dashboard Overdue"
        in response.data
    )


def test_overdue_task_stays_active(
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
            title="TEST - Overdue Carry Over",
            scheduled_date=yesterday,
            due_date=yesterday,
            status="on-going",
            priority="high",
            user_id=users["user_a_id"],
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    response = login_user_a.get(
        "/dashboard"
    )

    assert response.status_code == 200

    html = response.get_data(
        as_text=True
    )

    # Task appears on Dashboard.
    assert (
        f'data-bs-target="#taskDetailsModal{task_id}"'
        in html
    )

    # Overdue visual indicator exists.
    assert (
        "task-overdue-status"
        in html
    )

    # Database status remains On-going.
    with app.app_context():
        task = db.session.get(
            Task,
            task_id,
        )

        assert task.status == "on-going"


def test_all_status_filters(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    future = (
        today
        + timedelta(days=5)
    )

    with app.app_context():

        yet_task = Task(
            title="TEST - Status Yet",
            scheduled_date=future,
            due_date=future,
            status="yet-to-do",
            priority="medium",
            user_id=users["user_a_id"],
        )

        ongoing_task = Task(
            title="TEST - Status Ongoing",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        completed_task = Task(
            title="TEST - Status Finished",
            scheduled_date=today,
            due_date=today,
            status="completed",
            priority="medium",
            completed_at=datetime.now(
                NZ_TIMEZONE
            ),
            user_id=users["user_a_id"],
        )

        dropped_task = Task(
            title="TEST - Status Dropped",
            scheduled_date=today,
            due_date=today,
            status="dropped",
            priority="medium",
            user_id=users["user_a_id"],
        )

        db.session.add_all(
            [
                yet_task,
                ongoing_task,
                completed_task,
                dropped_task,
            ]
        )

        db.session.commit()

        task_ids = {
            "yet-to-do": yet_task.id,
            "on-going": ongoing_task.id,
            "completed": completed_task.id,
            "dropped": dropped_task.id,
        }

    for status, expected_id in (
        task_ids.items()
    ):
        response = login_user_a.get(
            "/tasks/",
            query_string={
                "status": status,
            },
        )

        assert response.status_code == 200

        html = response.get_data(
            as_text=True
        )

        assert (
            f'data-bs-target="#taskDetailsModal{expected_id}"'
            in html
        )

        for (
            other_status,
            other_id,
        ) in task_ids.items():

            if other_status == status:
                continue

            assert (
                f'data-bs-target="#taskDetailsModal{other_id}"'
                not in html
            )


def test_all_priority_filters(
    app,
    login_user_a,
    users,
):
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    with app.app_context():

        high_task = Task(
            title="TEST - Priority High",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="high",
            user_id=users["user_a_id"],
        )

        medium_task = Task(
            title="TEST - Priority Medium",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        low_task = Task(
            title="TEST - Priority Low",
            scheduled_date=today,
            due_date=today,
            status="on-going",
            priority="low",
            user_id=users["user_a_id"],
        )

        db.session.add_all(
            [
                high_task,
                medium_task,
                low_task,
            ]
        )

        db.session.commit()

        task_ids = {
            "high": high_task.id,
            "medium": medium_task.id,
            "low": low_task.id,
        }

    for priority, expected_id in (
        task_ids.items()
    ):
        response = login_user_a.get(
            "/tasks/",
            query_string={
                "priority": priority,
            },
        )

        assert response.status_code == 200

        html = response.get_data(
            as_text=True
        )

        assert (
            f'data-bs-target="#taskDetailsModal{expected_id}"'
            in html
        )

        for (
            other_priority,
            other_id,
        ) in task_ids.items():

            if other_priority == priority:
                continue

            assert (
                f'data-bs-target="#taskDetailsModal{other_id}"'
                not in html
            )


def test_due_date_filter(
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

    later = (
        today
        + timedelta(days=5)
    )

    with app.app_context():

        tomorrow_task = Task(
            title="TEST - Due Tomorrow",
            scheduled_date=today,
            due_date=tomorrow,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        later_task = Task(
            title="TEST - Due Later",
            scheduled_date=today,
            due_date=later,
            status="on-going",
            priority="medium",
            user_id=users["user_a_id"],
        )

        db.session.add_all(
            [
                tomorrow_task,
                later_task,
            ]
        )

        db.session.commit()

        tomorrow_id = tomorrow_task.id
        later_id = later_task.id

    response = login_user_a.get(
        "/tasks/",
        query_string={
            "due_date": tomorrow.isoformat(),
        },
    )

    assert response.status_code == 200

    html = response.get_data(
        as_text=True
    )

    assert (
        f'data-bs-target="#taskDetailsModal{tomorrow_id}"'
        in html
    )

    assert (
        f'data-bs-target="#taskDetailsModal{later_id}"'
        not in html
    )