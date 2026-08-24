from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask_login import current_user

from extensions import db
from models import Task


NZ_TIMEZONE = ZoneInfo("Pacific/Auckland")


def get_notifications():
    if not current_user.is_authenticated:
        return {
            "notifications": [],
            "notification_count": 0,
            "overdue_count": 0,
            "due_today_count": 0,
            "upcoming_count": 0,
        }

    today = datetime.now(NZ_TIMEZONE).date()

    # Upcoming = tomorrow through the next 3 days
    upcoming_end = today + timedelta(days=3)

    tasks = db.session.scalars(
        db.select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.status.notin_(
                ("completed", "dropped")
            ),
            Task.due_date <= upcoming_end,
        )
        .order_by(
            Task.due_date.asc(),
            Task.created_at.desc(),
        )
    ).all()

    notifications = []

    overdue_count = 0
    due_today_count = 0
    upcoming_count = 0

    for task in tasks:

        # OVERDUE
        if task.due_date < today:

            overdue_count += 1

            notifications.append(
                {
                    "type": "overdue",
                    "title": task.title,
                    "message": (
                        f"Overdue since "
                        f"{task.due_date.strftime('%d %b %Y')}"
                    ),
                    "task_id": task.id,
                }
            )

        # DUE TODAY
        elif task.due_date == today:

            due_today_count += 1

            notifications.append(
                {
                    "type": "today",
                    "title": task.title,
                    "message": "Due today",
                    "task_id": task.id,
                }
            )

        # UPCOMING
        else:

            upcoming_count += 1

            notifications.append(
                {
                    "type": "upcoming",
                    "title": task.title,
                    "message": (
                        "Due "
                        + task.due_date.strftime(
                            "%d %b %Y"
                        )
                    ),
                    "task_id": task.id,
                }
            )

    return {
        "notifications": notifications,
        "notification_count": len(notifications),
        "overdue_count": overdue_count,
        "due_today_count": due_today_count,
        "upcoming_count": upcoming_count,
    }