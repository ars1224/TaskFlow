from extensions import db
from models import User


def test_protected_dashboard_requires_login(
    client,
):
    response = client.get(
        "/dashboard",
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert "/auth/login" in response.headers[
        "Location"
    ]


def test_invalid_login_is_rejected(
    client,
    users,
):
    response = client.post(
        "/auth/login",
        data={
            "email": users["user_a_email"],
            "password": "WrongPassword123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    assert (
        b"Incorrect email or password."
        in response.data
    )


def test_duplicate_registration_is_rejected(
    app,
    client,
    users,
):
    response = client.post(
        "/auth/register",
        data={
            "full_name": "Duplicate User",
            "email": users["user_a_email"],
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    assert (
        b"An account with that email already exists."
        in response.data
    )

    with app.app_context():
        users_with_email = db.session.scalars(
            db.select(User).where(
                User.email
                == users["user_a_email"]
            )
        ).all()

        assert len(users_with_email) == 1


def test_successful_logout(
    login_user_a,
):
    # User should be authenticated first.
    response = login_user_a.get(
        "/dashboard",
        follow_redirects=False,
    )

    assert response.status_code == 200

    # Log out.
    response = login_user_a.post(
        "/auth/logout",
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert "/auth/login" in response.headers[
        "Location"
    ]

    # Dashboard must now be protected again.
    response = login_user_a.get(
        "/dashboard",
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert "/auth/login" in response.headers[
        "Location"
    ]


def test_remember_me_sets_cookie(
    client,
    users,
):
    response = client.post(
        "/auth/login",
        data={
            "email": users["user_a_email"],
            "password": users["password"],
            "remember": "on",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    cookies = response.headers.getlist(
        "Set-Cookie"
    )

    assert any(
        "remember_token=" in cookie
        for cookie in cookies
    )