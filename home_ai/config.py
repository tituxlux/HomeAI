from __future__ import annotations

import os
from pathlib import Path

from werkzeug.security import generate_password_hash


class Config:
    APP_NAME = "home_ai"
    SECRET_KEY = os.environ.get("HOME_AI_SECRET_KEY", "dev-home-ai-secret-key")

    APP_ROOT = Path(__file__).resolve().parent.parent
    GAR_CONFIG_PATH = os.environ.get("HOME_AI_GAR_CONFIG", str(APP_ROOT / "GAR" / "comptes" / "config.yml"))

    HOME_AI_ADMIN_USER = os.environ.get("HOME_AI_ADMIN_USER", "admin")
    HOME_AI_ADMIN_PASSWORD_HASH = os.environ.get(
        "HOME_AI_ADMIN_PASSWORD_HASH",
        generate_password_hash(os.environ.get("HOME_AI_ADMIN_PASSWORD", "admin")),
    )

    HOME_AI_DASHBOARD = {
        "version": 1,
        "grid": {"columns": 6, "rows": 10},
        "modules": {
            "collections": {
                "type": "collection_selector",
                "enabled": True,
                "placement": {"col": 1, "row": 1, "colspan": 2, "rowspan": 3},
            },
            "prompt": {
                "type": "prompt_editor",
                "enabled": True,
                "placement": {"col": 1, "row": 4, "colspan": 2, "rowspan": 2},
            },
            "conversations": {
                "type": "conversation_list",
                "enabled": True,
                "placement": {"col": 1, "row": 6, "colspan": 2, "rowspan": 5},
            },
            "chat": {
                "type": "chat",
                "enabled": True,
                "placement": {"col": 3, "row": 1, "colspan": 4, "rowspan": 10},
            },
        },
    }
