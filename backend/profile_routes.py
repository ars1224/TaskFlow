from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/profile",
)


@profile_bp.get("/")
@login_required
def view_profile():
    today = datetime.now().strftime("%A %d %B %Y")

    return render_template(
        "profile.html",
        today=today,
    )


@profile_bp.post("/update")
@login_required
def update_profile():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if len(full_name) < 2:
        flash("Please enter a valid full name.", "danger")
        return redirect(url_for("profile.view_profile"))

    if not email or "@" not in email:
        flash("Please enter a valid email address.", "danger")
        return redirect(url_for("profile.view_profile"))

    existing_user = db.session.scalar(
        db.select(User).where(
            func.lower(User.email) == email,
            User.id != current_user.id,
        )
    )

    if existing_user:
        flash("That email address is already being used.", "danger")
        return redirect(url_for("profile.view_profile"))

    current_user.full_name = full_name
    current_user.email = email

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("The profile could not be updated.", "danger")
    else:
        flash("Your profile has been updated successfully.", "success")

    return redirect(url_for("profile.view_profile"))


@profile_bp.post("/change-password")
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Your current password is incorrect.", "danger")
    elif len(new_password) < 8:
        flash("The new password must contain at least 8 characters.", "danger")
    elif new_password != confirm_password:
        flash("The new passwords do not match.", "danger")
    elif current_user.check_password(new_password):
        flash("Your new password must be different.", "danger")
    else:
        current_user.set_password(new_password)
        db.session.commit()

        flash("Your password has been changed successfully.", "success")

    return redirect(url_for("profile.view_profile"))