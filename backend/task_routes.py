from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Task


task_bp = Blueprint(
    "tasks",
    __name__,
    url_prefix="/tasks",
)

NZ_TIMEZONE = ZoneInfo("Pacific/Auckland")
VALID_PRIORITIES = {"low", "medium", "high"}

STATUS_LABELS = {
    "yet-to-do": "Yet-to-do",
    "on-going": "On-going",
    "completed": "Finished",
    "dropped": "Dropped",
}


def get_today():
    return datetime.now(NZ_TIMEZONE).date()


def get_today_tasks():
    priority_order = case(
        (Task.priority == "high", 1),
        (Task.priority == "medium", 2),
        else_=3,
    )

    return db.session.scalars(
        db.select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.scheduled_date == get_today(),
        )
        .order_by(
            priority_order,
            Task.created_at.desc(),
        )
    ).all()


@task_bp.get("/")
@login_required
def list_tasks():
    sync_today_task_statuses
    return render_template(
        "tasks/list.html",
        tasks=get_all_tasks(),
        today=get_today(),
        status_labels=STATUS_LABELS,
        form_data={},
        open_create_modal=request.args.get("create") == "1",
    )


@task_bp.post("/create")
@login_required
def create_task():
    return_to = request.form.get(
        "return_to",
        "tasks.list_tasks",
    )
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "").strip().lower()

    scheduled_date_value = request.form.get(
        "scheduled_date",
        "",
    ).strip()

    due_date_value = request.form.get(
        "due_date",
        "",
    ).strip()

    errors = []

    if not title:
        errors.append("Task title is required.")
    elif len(title) > 150:
        errors.append("Task title must contain 150 characters or fewer.")

    if len(description) > 2000:
        errors.append(
            "Task description must contain 2,000 characters or fewer."
        )

    if priority not in VALID_PRIORITIES:
        errors.append("Please select a valid priority.")

    # Scheduled date
    try:
        scheduled_date = datetime.strptime(
            scheduled_date_value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        scheduled_date = None
        errors.append(
            "Please select when you will do this task."
        )

    # Due date
    try:
        due_date = datetime.strptime(
            due_date_value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        due_date = None
        errors.append("Please select a valid due date.")

    # Scheduled date cannot be after the deadline
    if (
        scheduled_date is not None
        and due_date is not None
        and scheduled_date > due_date
    ):
        errors.append(
            "The scheduled date cannot be after the due date."
        )

    if errors:
        for error in errors:
            flash(error, "danger")

        return render_template(
            "tasks/list.html",
            tasks=get_all_tasks(),
            today=get_today(),
            status_labels=STATUS_LABELS,
            form_data=request.form,
            open_create_modal=True,
        ), 400

    task = Task(
        title=title,
        description=description or None,
        scheduled_date=scheduled_date,
        due_date=due_date,
        priority=priority,
        status=(
            "on-going"
            if scheduled_date == get_today()
            else "yet-to-do"
        ),
        user_id=current_user.id,
    )

    try:
        db.session.add(task)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "The task could not be saved. Please try again.",
            "danger",
        )

    else:
        flash(
            "Task created successfully.",
            "success",
        )


    if return_to == "main.dashboard":
        return redirect(
            url_for("main.dashboard")
        )

    return redirect(
        url_for("tasks.list_tasks")
    )

@task_bp.post("/<int:task_id>/edit")
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id,
    ).first_or_404()

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "").strip().lower()

    scheduled_date_value = request.form.get(
        "scheduled_date",
        "",
    ).strip()

    due_date_value = request.form.get(
        "due_date",
        "",
    ).strip()

    errors = []

    # Title validation
    if not title:
        errors.append("Task title is required.")
    elif len(title) > 150:
        errors.append(
            "Task title must contain 150 characters or fewer."
        )

    # Description validation
    if len(description) > 2000:
        errors.append(
            "Task description must contain 2,000 characters or fewer."
        )

    # Priority validation
    if priority not in VALID_PRIORITIES:
        errors.append("Please select a valid priority.")

    # Scheduled date validation
    try:
        scheduled_date = datetime.strptime(
            scheduled_date_value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        scheduled_date = None
        errors.append(
            "Please select when you will do this task."
        )

    # Due date validation
    try:
        due_date = datetime.strptime(
            due_date_value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        due_date = None
        errors.append(
            "Please select a valid due date."
        )

    # Scheduled date cannot be later than deadline
    if (
        scheduled_date is not None
        and due_date is not None
        and scheduled_date > due_date
    ):
        errors.append(
            "The scheduled date cannot be after the due date."
        )

    # Show validation errors
    if errors:
        for error in errors:
            flash(error, "danger")

        return redirect(
            request.referrer
            or url_for("tasks.list_tasks")
        )

    # Update task
    task.title = title
    task.description = description or None
    task.priority = priority
    task.scheduled_date = scheduled_date
    task.due_date = due_date

    if task.status not in {"completed", "dropped"}:
        if scheduled_date == get_today():
            task.status = "on-going"
        else:
            task.status = "yet-to-do"

    try:
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "The task could not be updated. Please try again.",
            "danger",
        )

    else:
        flash(
            "Task updated successfully.",
            "success",
        )

    return redirect(
        request.referrer
        or url_for("tasks.list_tasks")
    )

def get_all_tasks():
    priority_order = case(
        (Task.priority == "high", 1),
        (Task.priority == "medium", 2),
        else_=3,
    )

    return db.session.scalars(
        db.select(Task)
        .where(
            Task.user_id == current_user.id,
        )
        .order_by(
            Task.scheduled_date.asc(),
            priority_order,
            Task.due_date.asc(),
            Task.created_at.desc(),
        )
    ).all()

@task_bp.post("/<int:task_id>/delete")
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id,
    ).first_or_404()

    task.status = "dropped"

    try:
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "The task could not be dropped. Please try again.",
            "danger",
        )

    else:
        flash(
            "Task marked as dropped.",
            "success",
        )

    return redirect(
        request.referrer
        or url_for("tasks.list_tasks")
    )

def sync_today_task_statuses():
    today = get_today()

    tasks = db.session.scalars(
        db.select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.status == "yet-to-do",
            Task.scheduled_date == today,
        )
    ).all()

    if not tasks:
        return

    for task in tasks:
        task.status = "on-going"

    db.session.commit()


@task_bp.post("/<int:task_id>/toggle-complete")
@login_required
def toggle_complete(task_id):
    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id,
    ).first_or_404()

    # Dropped tasks cannot be completed
    if task.status == "dropped":
        flash(
            "Dropped tasks cannot be marked as finished.",
            "danger",
        )

        return redirect(
            request.referrer
            or url_for("tasks.list_tasks")
        )

    # Finished -> incomplete
    if task.status == "completed":
        task.completed_at = None

        if task.scheduled_date == get_today():
            task.status = "on-going"
        else:
            task.status = "yet-to-do"

    # Incomplete -> finished
    else:
        task.status = "completed"
        task.completed_at = datetime.now(NZ_TIMEZONE)

    try:
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "The task status could not be updated. Please try again.",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for("tasks.list_tasks")
    )