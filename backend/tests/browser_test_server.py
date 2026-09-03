from pathlib import Path
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


BACKEND_PATH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_PATH))

from app import create_app
from extensions import db
from models import Task, User


DATABASE_PATH = Path(__file__).resolve().parents[1] / ".browser_test.db"

app = create_app(
    {
        "TESTING": True,
        "SECRET_KEY": "taskflow-browser-test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{DATABASE_PATH.as_posix()}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "SESSION_COOKIE_SECURE": False,
        "REMEMBER_COOKIE_SECURE": False,
    }
)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if db.session.scalar(db.select(User).where(User.email == "browser@test.com")) is None:
            today = datetime.now(ZoneInfo("Pacific/Auckland")).date()
            user = User(full_name="Browser Test User", email="browser@test.com")
            user.set_password("BrowserTest123!")
            db.session.add(user)
            db.session.flush()

            db.session.add_all(
                [
                    Task(
                        title="Overdue assessment task",
                        description="Browser evidence for overdue handling.",
                        scheduled_date=today - timedelta(days=2),
                        due_date=today - timedelta(days=1),
                        status="on-going",
                        priority="high",
                        user_id=user.id,
                    ),
                    Task(
                        title="Due today assessment task",
                        scheduled_date=today,
                        due_date=today,
                        status="on-going",
                        priority="medium",
                        user_id=user.id,
                    ),
                    Task(
                        title="Upcoming assessment task",
                        scheduled_date=today,
                        due_date=today + timedelta(days=2),
                        status="yet-to-do",
                        priority="low",
                        user_id=user.id,
                    ),
                    Task(
                        title="Historical reflection task",
                        scheduled_date=today - timedelta(days=3),
                        due_date=today - timedelta(days=2),
                        status="completed",
                        priority="medium",
                        completed_at=datetime.now(ZoneInfo("Pacific/Auckland")) - timedelta(days=1),
                        remarks="Completed after revising the plan.",
                        reflection="Break large tasks into smaller scheduled steps.",
                        user_id=user.id,
                    ),
                ]
            )
            db.session.commit()

    app.run(host="127.0.0.1", port=5055, debug=False, use_reloader=False)
