from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from extensions import db
from models import Task, User


NZ_TIMEZONE = ZoneInfo("Pacific/Auckland")


def test_tc01_valid_registration_creates_account(app, client):
    response = client.post(
        "/auth/register",
        data={
            "full_name": "Assessment User",
            "email": "assessment@test.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Your TaskFlow account has been created." in response.data

    with app.app_context():
        user = db.session.scalar(
            db.select(User).where(User.email == "assessment@test.com")
        )
        assert user is not None
        assert user.check_password("Password123!")


def test_tc03_valid_login_starts_authenticated_session(client, users):
    response = client.post(
        "/auth/login",
        data={
            "email": users["user_a_email"],
            "password": users["password"],
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Welcome back!" in response.data
    assert b"Daily Progress" in response.data


def test_tc19_notification_categories_are_generated(
    app,
    login_user_a,
    users,
):
    today = datetime.now(NZ_TIMEZONE).date()

    with app.app_context():
        tasks = [
            Task(
                title="TEST - Notification Overdue",
                scheduled_date=today - timedelta(days=2),
                due_date=today - timedelta(days=1),
                status="on-going",
                priority="high",
                user_id=users["user_a_id"],
            ),
            Task(
                title="TEST - Notification Today",
                scheduled_date=today,
                due_date=today,
                status="on-going",
                priority="medium",
                user_id=users["user_a_id"],
            ),
            Task(
                title="TEST - Notification Upcoming",
                scheduled_date=today,
                due_date=today + timedelta(days=2),
                status="on-going",
                priority="low",
                user_id=users["user_a_id"],
            ),
        ]
        db.session.add_all(tasks)
        db.session.commit()

    response = login_user_a.get("/dashboard")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "TEST - Notification Overdue" in html
    assert "Overdue since" in html
    assert "TEST - Notification Today" in html
    assert "Due today" in html
    assert "TEST - Notification Upcoming" in html
    assert "Due " in html


def test_tc21_profile_update_persists(app, login_user_a, users):
    response = login_user_a.post(
        "/profile/update",
        data={
            "full_name": "Updated Assessment User",
            "email": "updated-user-a@test.com",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Your profile has been updated successfully." in response.data

    with app.app_context():
        user = db.session.get(User, users["user_a_id"])
        assert user.full_name == "Updated Assessment User"
        assert user.email == "updated-user-a@test.com"


def test_tc22_password_update_invalidates_old_password(
    client,
    login_user_a,
    users,
):
    response = login_user_a.post(
        "/profile/change-password",
        data={
            "current_password": users["password"],
            "new_password": "NewPassword456!",
            "confirm_password": "NewPassword456!",
        },
        follow_redirects=True,
    )
    assert b"Your password has been changed successfully." in response.data

    login_user_a.post("/auth/logout")

    old_login = client.post(
        "/auth/login",
        data={
            "email": users["user_a_email"],
            "password": users["password"],
        },
        follow_redirects=True,
    )
    assert b"Incorrect email or password." in old_login.data

    new_login = client.post(
        "/auth/login",
        data={
            "email": users["user_a_email"],
            "password": "NewPassword456!",
        },
        follow_redirects=True,
    )
    assert b"Welcome back!" in new_login.data


def test_tc23_task_persists_across_logout_and_login(
    app,
    client,
    login_user_a,
    users,
):
    today = datetime.now(NZ_TIMEZONE).date()

    create_response = login_user_a.post(
        "/tasks/create",
        data={
            "title": "TEST - Persistent Task",
            "description": "Must survive a new authenticated session.",
            "priority": "high",
            "scheduled_date": today.isoformat(),
            "due_date": today.isoformat(),
        },
        follow_redirects=True,
    )
    assert create_response.status_code == 200

    login_user_a.post("/auth/logout")
    login_response = client.post(
        "/auth/login",
        data={
            "email": users["user_a_email"],
            "password": users["password"],
        },
        follow_redirects=True,
    )
    assert b"Welcome back!" in login_response.data

    task_list = client.get("/tasks/")
    assert b"TEST - Persistent Task" in task_list.data

    with app.app_context():
        task = db.session.scalar(
            db.select(Task).where(Task.title == "TEST - Persistent Task")
        )
        assert task is not None
        assert task.user_id == users["user_a_id"]


def test_tc17_past_dropped_task_appears_in_history(
    app,
    login_user_a,
    users,
):
    today = datetime.now(NZ_TIMEZONE).date()

    with app.app_context():
        task = Task(
            title="TEST - Dropped History",
            scheduled_date=today - timedelta(days=1),
            due_date=today - timedelta(days=1),
            status="dropped",
            priority="low",
            user_id=users["user_a_id"],
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    response = login_user_a.get("/tasks/history")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert f'id="taskDetailsModal{task_id}"' in html
