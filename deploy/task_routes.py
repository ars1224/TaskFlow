from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, case, or_
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


def get_day_bounds(day):
    start = datetime.combine(
        day,
        time.min,
        tzinfo=NZ_TIMEZONE,
    )

    end = start + timedelta(days=1)

    return start, end


def get_task_activity_date(task):
    # Finished tasks belong to the day
    # they were actually completed.
    if (
        task.status == "completed"
        and task.completed_at is not None
    ):
        completed_at = task.completed_at

        if completed_at.tzinfo is not None:
            completed_at = completed_at.astimezone(
                NZ_TIMEZONE
            )

        return completed_at.date()

    # Active and dropped tasks continue using
    # their planned scheduled date.
    return task.scheduled_date


def build_task_groups(tasks, today):
    groups = {}

    priority_rank = {
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    for task in tasks:
        activity_date = get_task_activity_date(
            task
        )

        groups.setdefault(
            activity_date,
            [],
        ).append(task)

    # Priority order inside each date.
    for date_tasks in groups.values():
        date_tasks.sort(
            key=lambda task: (
                priority_rank.get(
                    task.priority,
                    4,
                ),
                task.due_date,
                -task.id,
            )
        )

    def group_sort_key(item):
        task_date = item[0]

        # Today always first.
        if task_date == today:
            return (
                0,
                0,
            )

        # Carry-over/overdue dates next.
        # Most recent first.
        if task_date < today:
            return (
                1,
                -task_date.toordinal(),
            )

        # Future dates last.
        return (
            2,
            task_date.toordinal(),
        )

    return sorted(
        groups.items(),
        key=group_sort_key,
    )


@task_bp.get("/")
@login_required
def list_tasks():
    sync_today_task_statuses()

    today = get_today()

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

    task_groups = build_task_groups(
        tasks,
        today,
    )

    filters_active = any(
        [
            search,
            selected_statuses,
            selected_priorities,
            due_date_value,
        ]
    )

    return render_template(
        "tasks/list.html",

        tasks=tasks,
        task_groups=task_groups,

        today=today,
        status_labels=STATUS_LABELS,

        form_data={},

        open_create_modal=(
            request.args.get("create") == "1"
        ),

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

    # Scheduled date cannot be in the past.
    if (
        scheduled_date is not None
        and scheduled_date < get_today()
    ):
        errors.append(
            "The scheduled date cannot be in the past."
        )

    # Scheduled date cannot be after due date.
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

        today = get_today()
        tasks = get_all_tasks()

        task_groups = build_task_groups(
            tasks,
            today,
        )

        return render_template(
            "tasks/list.html",

            tasks=tasks,
            task_groups=task_groups,

            today=today,
            status_labels=STATUS_LABELS,

            form_data=request.form,
            open_create_modal=True,

            search="",
            selected_statuses=[],
            selected_priorities=[],
            selected_due_date="",
            filters_active=False,
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

    # Scheduled date cannot be in the past.
    if (
        scheduled_date is not None
        and scheduled_date < get_today()
    ):
        errors.append(
            "The scheduled date cannot be in the past."
        )

    # Scheduled date cannot be after due date.
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
        if scheduled_date <= get_today():
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

    today_start, tomorrow_start = (
        get_day_bounds(today)
    )

    statuses = statuses or []
    priorities = priorities or []

    priority_order = case(
        (Task.priority == "high", 1),
        (Task.priority == "medium", 2),
        else_=3,
    )

    query = db.select(Task).where(
        Task.user_id == current_user.id,

        or_(
            # -----------------------------------------
            # ACTIVE TASKS
            #
            # They always stay on Task List,
            # even when their scheduled date passed.
            # -----------------------------------------
            Task.status.in_(
                (
                    "yet-to-do",
                    "on-going",
                )
            ),

            # -----------------------------------------
            # FINISHED TODAY
            #
            # The original scheduled date does not
            # matter anymore for today's activity.
            # -----------------------------------------
            and_(
                Task.status == "completed",
                Task.completed_at >= today_start,
                Task.completed_at < tomorrow_start,
            ),

            # Backward compatibility for any old
            # completed task without completed_at.
            and_(
                Task.status == "completed",
                Task.completed_at.is_(None),
                Task.scheduled_date >= today,
            ),

            # -----------------------------------------
            # DROPPED TASKS
            #
            # Keep the current scheduled-date rule.
            # -----------------------------------------
            and_(
                Task.status == "dropped",
                Task.scheduled_date >= today,
            ),
        ),
    )

    # Search
    if search:
        query = query.where(
            Task.title.ilike(
                f"%{search}%"
            )
        )

    # Status filters
    valid_statuses = [
        status
        for status in statuses
        if status in STATUS_LABELS
    ]

    if valid_statuses:
        query = query.where(
            Task.status.in_(
                valid_statuses
            )
        )

    # Priority filters
    valid_priorities = [
        priority
        for priority in priorities
        if priority in VALID_PRIORITIES
    ]

    if valid_priorities:
        query = query.where(
            Task.priority.in_(
                valid_priorities
            )
        )

    # Due date filter
    if due_date is not None:
        query = query.where(
            Task.due_date == due_date
        )

    query = query.order_by(
        priority_order,
        Task.due_date.asc(),
        Task.created_at.desc(),
    )

    return db.session.scalars(
        query
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
            Task.scheduled_date <= today,
        )
    ).all()

    if not tasks:
        return

    for task in tasks:
        task.status = "on-going"

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()


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

        if task.scheduled_date <= get_today():
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

    today_start, _ = get_day_bounds(
        today
    )

    search = request.args.get(
        "q",
        "",
    ).strip()

    query = db.select(Task).where(
        Task.user_id == current_user.id,

        or_(
            # Finished before today.
            and_(
                Task.status == "completed",
                Task.completed_at.is_not(None),
                Task.completed_at < today_start,
            ),

            # Old completed records which existed
            # before completed_at was introduced.
            and_(
                Task.status == "completed",
                Task.completed_at.is_(None),
                Task.scheduled_date < today,
            ),

            # Dropped records.
            and_(
                Task.status == "dropped",
                Task.scheduled_date < today,
            ),
        ),
    )

    if search:
        query = query.where(
            Task.title.ilike(
                f"%{search}%"
            )
        )

    history_tasks = db.session.scalars(
        query
    ).all()

    # Sort History by actual activity date.
    history_tasks.sort(
        key=lambda task: (
            get_task_activity_date(task),
            task.created_at,
        ),
        reverse=True,
    )

    history_groups = []

    for task in history_tasks:
        activity_date = (
            get_task_activity_date(task)
        )

        if (
            not history_groups
            or history_groups[-1][0]
            != activity_date
        ):
            history_groups.append(
                (
                    activity_date,
                    [task],
                )
            )

        else:
            history_groups[-1][1].append(
                task
            )

    return render_template(
        "tasks/history.html",
        history_groups=history_groups,
        today=today,
        status_labels=STATUS_LABELS,
        search=search,
    )