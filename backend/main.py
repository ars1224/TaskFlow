from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Task


main_bp = Blueprint(
    "main",
    __name__,
)

NZ_TIMEZONE = ZoneInfo(
    "Pacific/Auckland"
)


@main_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    return redirect(
        url_for("auth.login")
    )


def completed_on_date(task, target_date):
    if task.completed_at is None:
        return False

    completed_at = task.completed_at

    if completed_at.tzinfo is not None:
        completed_at = completed_at.astimezone(
            NZ_TIMEZONE
        )

    return completed_at.date() == target_date


@main_bp.get("/dashboard")
@login_required
def dashboard():
    today = datetime.now(
        NZ_TIMEZONE
    ).date()

    tasks = db.session.scalars(
        db.select(Task)
        .where(
            Task.user_id == current_user.id
        )
        .order_by(
            Task.due_date.asc(),
            Task.created_at.desc(),
        )
    ).all()


    # -------------------------------------------------
    # UPDATE ACTIVE TASKS
    #
    # Any unfinished task whose scheduled date has
    # arrived becomes On-going.
    # -------------------------------------------------

    status_changed = False

    for task in tasks:
        if (
            task.status == "yet-to-do"
            and task.scheduled_date <= today
        ):
            task.status = "on-going"
            status_changed = True

    if status_changed:
        db.session.commit()


    def task_status(task):
        return task.status.strip().lower()


    # -------------------------------------------------
    # TASKS ORIGINALLY SCHEDULED FOR TODAY
    # -------------------------------------------------

    scheduled_today_tasks = [
        task
        for task in tasks
        if task.scheduled_date == today
    ]


    # -------------------------------------------------
    # TASKS ACTUALLY COMPLETED TODAY
    #
    # Includes:
    # - tasks scheduled today
    # - overdue tasks finished today
    # - future tasks finished early today
    # -------------------------------------------------

    completed_today_tasks = [
        task
        for task in tasks
        if (
            task_status(task) == "completed"
            and completed_on_date(
                task,
                today,
            )
        )
    ]


    # -------------------------------------------------
    # DASHBOARD DISPLAY TASKS
    #
    # Show:
    # - today's scheduled tasks
    # - unfinished carry-over tasks
    # - anything completed today
    # -------------------------------------------------

    dashboard_task_ids = set()
    dashboard_tasks = []

    for task in tasks:

        scheduled_today = (
            task.scheduled_date == today
        )

        carry_over = (
            task.scheduled_date < today
            and task_status(task)
            in {
                "yet-to-do",
                "on-going",
            }
        )

        completed_today = (
            task_status(task) == "completed"
            and completed_on_date(
                task,
                today,
            )
        )

        if (
            scheduled_today
            or carry_over
            or completed_today
        ):
            if task.id not in dashboard_task_ids:
                dashboard_task_ids.add(
                    task.id
                )

                dashboard_tasks.append(
                    task
                )


    # -------------------------------------------------
    # DAILY STATUS COUNTS
    #
    # Planned-today tasks use scheduled_date.
    #
    # Finished also includes tasks completed early
    # today, regardless of original scheduled date.
    # -------------------------------------------------

    yet_to_do = sum(
        task_status(task) == "yet-to-do"
        for task in scheduled_today_tasks
    )

    on_going = sum(
        task_status(task) == "on-going"
        for task in scheduled_today_tasks
    )

    dropped = sum(
        task_status(task) == "dropped"
        for task in scheduled_today_tasks
    )

    completed = len(
        completed_today_tasks
    )


    # -------------------------------------------------
    # OVERDUE
    #
    # Overdue remains an On-going task internally.
    # -------------------------------------------------

    overdue = sum(
        task.due_date < today
        and task_status(task)
        not in {
            "completed",
            "dropped",
        }
        for task in tasks
    )


    # -------------------------------------------------
    # DAILY PROGRESS
    #
    # Include:
    # - today's scheduled non-dropped tasks
    # - future/carry-over tasks completed today
    #
    # Avoid counting the same task twice.
    # -------------------------------------------------

    progress_task_ids = {
        task.id
        for task in scheduled_today_tasks
        if task_status(task) != "dropped"
    }

    progress_task_ids.update(
        task.id
        for task in completed_today_tasks
    )

    total_today = len(
        progress_task_ids
    )

    completed_today = len(
        {
            task.id
            for task in completed_today_tasks
            if task.id in progress_task_ids
        }
    )

    daily_progress = (
        round(
            (
                completed_today
                / total_today
            )
            * 100
        )
        if total_today
        else 0
    )


    counts = {
        "yet_to_do": yet_to_do,
        "on_going": on_going,
        "completed": completed,
        "dropped": dropped,

        "pending": sum(
            task_status(task)
            in {
                "yet-to-do",
                "on-going",
            }
            for task in scheduled_today_tasks
        ),

        "overdue": overdue,
    }


    return render_template(
        "dashboard.html",

        today=today,

        today_tasks=scheduled_today_tasks,
        dashboard_tasks=dashboard_tasks,

        completed_today=completed_today,
        total_today=total_today,
        daily_progress=daily_progress,

        counts=counts,

        form_data={},
        open_create_modal=False,
    )