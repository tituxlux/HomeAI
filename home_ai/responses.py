from __future__ import annotations

from typing import Any

from flask import jsonify


def ok_response(data: dict[str, Any] | None = None, message: str = "", status_code: int = 200):
    payload = {
        "success": True,
        "status": "success",
        "data": data or {},
        "message": {"text": message, "type": "success"},
    }
    return jsonify(payload), status_code


def fail_response(reason: str, status_code: int = 400):
    payload = {
        "success": False,
        "status": "error",
        "error": reason,
        "message": {"text": reason, "type": "error"},
        "data": {},
    }
    return jsonify(payload), status_code
