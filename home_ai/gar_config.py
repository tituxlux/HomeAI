from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from flask import current_app


def load_gar_config() -> dict[str, Any]:
    try:
        with open(current_app.config["GAR_CONFIG_PATH"], "r", encoding="utf-8") as fp:
            loaded = yaml.safe_load(fp) or {}
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def comptes_dir() -> Path:
    return Path(current_app.config["APP_ROOT"]) / "GAR" / "comptes"


def project_name() -> str:
    return load_gar_config().get("project", {}).get("name", "Home AI")
