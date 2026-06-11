from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, current_app, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash


auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.login"


@dataclass
class AdminUser(UserMixin):
    username: str = "admin"

    @property
    def id(self) -> str:
        return self.username


def init_login(app):
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        if user_id == app.config["HOME_AI_ADMIN_USER"]:
            return AdminUser(username=user_id)
        return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        expected_user = current_app.config["HOME_AI_ADMIN_USER"]
        expected_hash = current_app.config["HOME_AI_ADMIN_PASSWORD_HASH"]
        if username == expected_user and check_password_hash(expected_hash, password):
            login_user(AdminUser(username=username))
            next_url = request.args.get("next") or url_for("chatbot.chat")
            return redirect(next_url)
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


def default_admin_password_hash() -> str:
    return generate_password_hash("admin")
