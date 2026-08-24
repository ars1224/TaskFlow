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
    sync_today_task_statuses()

    search = request.args.get(
        "q",
        "",
    ).strip()

    selected_statuses = request.args.getlist(
        "status"
    )

    selected_priorities = request.args.getlist(
        "priority"
    )

    due_date_value = request.args.get(
        "due_date",
        "",
    ).strip()

    due_date = None

    if due_date_value:
        try:
            due_date = datetime.strptime(
                due_date_value,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            due_date_value = ""

    tasks = get_all_tasks(
        search=search,
        statuses=selected_statuses,
        priorities=selected_priorities,
        due_date=due_date,
    )

    filters_active = any(
        [
            selected_statuses,
            selected_priorities,
            due_date_value,
        ]
    )

    return render_template(
        "tasks/list.html",
        tasks=tasks,
        today=get_today(),
        status_labels=STATUS_LABELS,
        form_data={},
        open_create_modal=request.args.get("create") == "1",

        search=search,
        selected_statuses=selected_statuses,
        selected_priorities=selected_priorities,
        selected_due_date=due_date_value,
        filters_active=filters_active,
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

def get_all_tasks(
    search="",
    statuses=None,
    priorities=None,
    due_date=None,
):
    today = get_today()

    statuses = statuses or []
    priorities = priorities or []

    priority_order = case(
        (Task.priority == "high", 1),
        (Task.priority == "medium", 2),
        else_=3,
    )

    query = db.select(Task).where(
        Task.user_id == current_user.id,

        # Task List contains today + future only
        Task.scheduled_date >= get_today(),
    )

    # Search by title
    if search:
        query = query.where(
            Task.title.ilike(f"%{search}%")
        )

    # Multiple status filters
    valid_statuses = [
        status
        for status in statuses
        if status in STATUS_LABELS
    ]

    if valid_statuses:
        query = query.where(
            Task.status.in_(valid_statuses)
        )

    # Multiple priority filters
    valid_priorities = [
        priority
        for priority in priorities
        if priority in VALID_PRIORITIES
    ]

    if valid_priorities:
        query = query.where(
            Task.priority.in_(valid_priorities)
        )

    # Due date
    if due_date is not None:
        query = query.where(
            Task.due_date == due_date
        )

    # Always date first, then priority
    query = query.order_by(
        Task.scheduled_date.asc(),
        priority_order,
        Task.due_date.asc(),
        Task.created_at.desc(),
    )

    return db.session.scalars(query).all()
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

@task_bp.post("/<int:task_id>/review")
@login_required
def review_task(task_id):
    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id,
    ).first_or_404()

    status = request.form.get(
        "status",
        task.status,
    ).strip().lower()

    priority = request.form.get(
        "priority",
        task.priority,
    ).strip().lower()

    remarks = request.form.get(
        "remarks",
        "",
    ).strip()

    reflection = request.form.get(
        "reflection",
        "",
    ).strip()

    errors = []

    if status not in STATUS_LABELS:
        errors.append(
            "Please select a valid task status."
        )

    if priority not in VALID_PRIORITIES:
        errors.append(
            "Please select a valid priority."
        )

    if len(remarks) > 2000:
        errors.append(
            "Remarks must contain 2,000 characters or fewer."
        )

    if len(reflection) > 2000:
        errors.append(
            "Reflection must contain 2,000 characters or fewer."
        )

    # Historical incomplete tasks should have a remark
    if (
        status in {"yet-to-do", "on-going"}
        and task.scheduled_date < get_today()
        and not remarks
    ):
        errors.append(
            "Please add a remark for an incomplete task."
        )

    if errors:
        for error in errors:
            flash(error, "danger")

        return redirect(
            request.referrer
            or url_for("tasks.task_history")
        )

    task.status = status
    task.priority = priority
    task.remarks = remarks or None
    task.reflection = reflection or None

    # Keep completed_at consistent
    if status == "completed":

        if task.completed_at is None:
            task.completed_at = datetime.now(
                NZ_TIMEZONE
            )

    else:
        task.completed_at = None

    try:
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "The task review could not be saved. Please try again.",
            "danger",
        )

    else:
        flash(
            "Task review saved successfully.",
            "success",
        )

    return redirect(
        request.referrer
        or url_for("tasks.task_history")
    )

@task_bp.get("/history")
@login_required
def task_history():
    today = get_today()

    search = request.args.get(
        "q",
        "",
    ).strip()

    query = db.select(Task).where(
        Task.user_id == current_user.id,
        Task.scheduled_date < today,
    )

    # Search by task title
    if search:
        query = query.where(
            Task.title.ilike(f"%{search}%")
        )

    history_tasks = db.session.scalars(
        query.order_by(
            Task.scheduled_date.desc(),
            Task.created_at.desc(),
        )
    ).all()

    history_groups = []

    for task in history_tasks:
        if (
            not history_groups
            or history_groups[-1][0] != task.scheduled_date
        ):
            history_groups.append(
                (
                    task.scheduled_date,
                    [task],
                )
            )
        else:
            history_groups[-1][1].append(task)

    return render_template(
        "tasks/history.html",
        history_groups=history_groups,
        today=today,
        status_labels=STATUS_LABELS,
        search=search,
    )