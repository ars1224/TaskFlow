from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(full_name) < 2:
            flash("Please enter your full name.", "danger")
        elif not email or "@" not in email:
            flash("Please enter a valid email address.", "danger")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        else:
            existing_user = db.session.scalar(
                db.select(User).where(func.lower(User.email) == email)
            )

            if existing_user:
                flash("An account with that email already exists.", "danger")
            else:
                user = User(full_name=full_name, email=email)
                user.set_password(password)

                try:
                    db.session.add(user)
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    flash("An account with that email already exists.", "danger")
                else:
                    login_user(user)
                    flash("Your TaskFlow account has been created.", "success")
                    return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = db.session.scalar(
            db.select(User).where(func.lower(User.email) == email)
        )

        if user is None or not user.check_password(password):
            flash("Incorrect email or password.", "danger")
        else:
            login_user(user, remember=remember)
            flash("Welcome back!", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))