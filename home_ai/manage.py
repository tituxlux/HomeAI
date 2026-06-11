from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, render_template
from flask_login import login_required

from home_ai.gar_config import comptes_dir, load_gar_config, project_name
from home_ai.responses import fail_response, ok_response


manage_bp = Blueprint("manage", __name__, url_prefix="/manage")


@manage_bp.route("/ingestors", methods=["GET"])
@login_required
def ingestors():
    config = load_gar_config()
    return render_template(
        "manage/ingestors.html",
        project_name=project_name(),
        data_sources=config.get("data_sources", []),
        vector_db=config.get("vector_db", {}),
        embedding=config.get("embedding", {}),
        model=config.get("model", {}),
    )


@manage_bp.route("/ingestors/run", methods=["POST"])
@login_required
def run_ingestor():
    job = _job_state()
    process = job.get("process")
    if process is not None and process.poll() is None:
        return fail_response("Ingestion is already running.", status_code=409)

    log_path = _ingest_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = current_app.config.get("HOME_AI_INGEST_COMMAND") or [sys.executable, "ingest.py"]
    try:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n--- ingest started {datetime.now(timezone.utc).isoformat()} ---\n")
            process = subprocess.Popen(
                command,
                cwd=str(comptes_dir()),
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
    except Exception as exc:
        current_app.logger.exception("Failed to start ingestion")
        return fail_response(f"Could not start ingestion: {exc}", status_code=500)

    job.clear()
    job.update({"process": process, "started_at": datetime.now(timezone.utc).isoformat(), "log_path": str(log_path)})
    return ok_response(_status_payload(job), message="Ingestion started.")


@manage_bp.route("/ingestors/status", methods=["GET"])
@login_required
def ingestor_status():
    return ok_response(_status_payload(_job_state()))


def _job_state() -> dict[str, Any]:
    return current_app.extensions.setdefault("home_ai_ingest_job", {})


def _status_payload(job: dict[str, Any]) -> dict[str, Any]:
    process = job.get("process")
    running = bool(process is not None and process.poll() is None)
    return_code = None if process is None or running else process.returncode
    return {
        "running": running,
        "return_code": return_code,
        "started_at": job.get("started_at"),
        "log": _read_log_tail(Path(job.get("log_path") or _ingest_log_path())),
    }


def _ingest_log_path() -> Path:
    return Path(current_app.config["APP_ROOT"]) / "logs" / "home_ai_ingest.log"


def _read_log_tail(path: Path, max_chars: int = 6000) -> str:
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return text[-max_chars:]
