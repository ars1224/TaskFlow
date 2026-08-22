from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):

    tasks = db.relationship(
    "Task",
    back_populates="owner",
    cascade="all, delete-orphan",
    lazy="select",
)
    
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    __tablename__ = "tasks"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('yet-to-do', 'on-going', 'completed', 'dropped')",
            name="ck_tasks_status",
        ),
        db.CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="ck_tasks_priority",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(150),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    scheduled_date = db.Column(
    db.Date,
    nullable=False,
    index=True,
    )

    due_date = db.Column(
        db.Date,
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="yet-to-do",
        index=True,
    )

    priority = db.Column(
        db.String(10),
        nullable=False,
        default="medium",
        index=True,
    )

    remarks = db.Column(
        db.Text,
        nullable=True,
    )

    reflection = db.Column(
        db.Text,
        nullable=True,
    )

    image_filename = db.Column(
        db.String(255),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner = db.relationship(
        "User",
        back_populates="tasks",
    )

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None