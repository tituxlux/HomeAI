from __future__ import annotations

from flask import Flask, redirect, url_for

from home_ai.auth import auth_bp, init_login
from home_ai.chatbot import chatbot_bp
from home_ai.config import Config
from home_ai.manage import manage_bp


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    init_login(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(manage_bp)

    @app.route("/")
    def home():
        return redirect(url_for("chatbot.chat"))

    return app
