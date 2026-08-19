from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case
from sqlalchemy.exc import SQLAlchemyError

from flask import render_template
from flask_login import current_user, login_required


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
            Task.due_date == get_today(),
        )
        .order_by(
            priority_order,
            Task.created_at.desc(),
        )
    ).all()


@task_bp.get("/")
@login_required
def list_tasks():
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
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "").strip().lower()
    due_date_value = request.form.get("due_date", "").strip()

    errors = []

    if not title:
        errors.append("Task title is required.")
    elif len(title) > 150:
        errors.append("Task title must contain 150 characters or fewer.")

    if len(description) > 2000:
        errors.append("Task description must contain 2,000 characters or fewer.")

    if priority not in VALID_PRIORITIES:
        errors.append("Please select a valid priority.")

    try:
        due_date = datetime.strptime(
            due_date_value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        due_date = None
        errors.append("Please select a valid due date.")

    if errors:
        for error in errors:
            flash(error, "danger")

        return render_template(
            "tasks/list.html",
            tasks=get_today_tasks(),
            today=get_today(),
            status_labels=STATUS_LABELS,
            form_data=request.form,
            open_create_modal=True,
        ), 400

    task = Task(
        title=title,
        description=description or None,
        due_date=due_date,
        priority=priority,
        status="yet-to-do",
        user_id=current_user.id,
    )

    try:
        db.session.add(task)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("The task could not be saved. Please try again.", "danger")
    else:
        flash("Task created successfully.", "success")

    return redirect(url_for("tasks.list_tasks"))

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
    due_date_value = request.form.get("due_date", "").strip()

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

    try:
        due_date = datetime.strptime(
            due_date_value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        due_date = None
        errors.append("Please select a valid due date.")

    if errors:
        for error in errors:
            flash(error, "danger")

        return redirect(
            request.referrer or url_for("tasks.list_tasks")
        )

    task.title = title
    task.description = description or None
    task.priority = priority
    task.due_date = due_date

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "The task could not be updated. Please try again.",
            "danger",
        )
    else:
        flash("Task updated successfully.", "success")

    return redirect(
        request.referrer or url_for("tasks.list_tasks")
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
            Task.due_date.asc(),
            priority_order,
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

    try:
        db.session.delete(task)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "The task could not be deleted. Please try again.",
            "danger",
        )
    else:
        flash("Task deleted successfully.", "success")

    return redirect(
        request.referrer or url_for("tasks.list_tasks")
    )