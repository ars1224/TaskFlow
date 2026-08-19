from datetime import datetime

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from datetime import datetime
from zoneinfo import ZoneInfo

from flask_login import current_user, login_required

from extensions import db
from models import Task


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    return redirect(url_for("auth.login"))


@main_bp.get("/dashboard")
@login_required
def dashboard():
    today = datetime.now(
        ZoneInfo("Pacific/Auckland")
    ).date()

    tasks = db.session.scalars(
        db.select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.due_date.asc(), Task.created_at.desc())
    ).all()

    today_tasks = [
        task for task in tasks
        if task.due_date == today
    ]

    def task_status(task):
        return task.status.strip().lower()

    yet_to_do = sum(
        task_status(task) == "yet-to-do"
        for task in tasks
    )
    on_going = sum(
        task_status(task) == "on-going"
        for task in tasks
    )
    completed = sum(
        task_status(task) == "completed"
        for task in tasks
    )
    dropped = sum(
        task_status(task) == "dropped"
        for task in tasks
    )

    overdue = sum(
        task.due_date < today
        and task_status(task) not in {"completed", "dropped"}
        for task in tasks
    )

    completed_today = sum(
        task_status(task) == "completed"
        for task in today_tasks
    )

    daily_progress = (
        round((completed_today / len(today_tasks)) * 100)
        if today_tasks
        else 0
    )

    counts = {
        "yet_to_do": yet_to_do,
        "on_going": on_going,
        "completed": completed,
        "dropped": dropped,
        "pending": yet_to_do + on_going,
        "overdue": overdue,
    }

    return render_template(
        "dashboard.html",
        today=today,
        today_tasks=today_tasks,
        completed_today=completed_today,
        daily_progress=daily_progress,
        counts=counts,
    )