from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Blueprint, current_app, render_template, request, session
from flask_login import login_required

from home_ai.gar_config import load_gar_config, project_name
from home_ai.responses import fail_response, ok_response


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


@chatbot_bp.route("/chat", methods=["GET"])
@login_required
def chat():
    return render_template(
        "chatbot/chat.html",
        dashboard=current_app.config["HOME_AI_DASHBOARD"],
        project_name=project_name(),
    )


@chatbot_bp.route("/chat", methods=["POST"])
@login_required
def chat_answer():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return fail_response("No message provided", status_code=400)

    conversation_id = _normalize_id(data.get("conversation_id"))
    selected_collections = _normalize_list(data.get("selected_collections"))
    selected_groups = _normalize_list(data.get("selected_groups"))
    if selected_groups and not selected_collections:
        selected_collections = _collections_for_groups(selected_groups)

    convo_state = _load_conversations()
    if not conversation_id:
        conversation_id = convo_state.get("current_id")
    if not conversation_id:
        conversation_id = _create_conversation(convo_state)

    try:
        chat_client = _get_chat_client()
        results = chat_client.query_vector_db(
            user_message,
            n_results=current_app.config.get("HOME_AI_VECTOR_RESULTS", 5),
        )
        context, sources = _context_and_sources(results, selected_collections)
        if not context:
            answer = "No relevant documents found in the local vector database."
        else:
            preprompt = _preferences().get("user_preprompt", "")
            prompt = "\n\n".join(part for part in [preprompt, context] if part)
            answer = chat_client.generate_answer(user_message, prompt)
    except Exception as exc:
        current_app.logger.exception("Error generating chatbot response")
        return fail_response(f"Chat failed: {exc}", status_code=500)

    _append_conversation_turn(convo_state, conversation_id, user_message, answer)
    _save_conversations(convo_state)
    return ok_response(
        {
            "response": answer,
            "sources": sources,
            "next_step": "",
            "structured": {},
            "correction": {},
            "conversation_id": conversation_id,
            "conversations": convo_state.get("items", []),
        }
    )


@chatbot_bp.route("/preferences", methods=["GET"])
@login_required
def get_preferences():
    prefs = _preferences()
    collections = _list_collections()
    groups = _collection_groups(collections)
    convo_state = _load_conversations()
    current_id = convo_state.get("current_id")
    return ok_response(
        {
            "collections": collections,
            "selected_collections": prefs.get("selected_collections", []),
            "collection_groups": groups,
            "selected_groups": prefs.get("selected_groups", []),
            "conversations": convo_state.get("items", []),
            "current_conversation": current_id,
            "current_history": _get_conversation_history(convo_state, current_id),
            "user_preprompt": prefs.get("user_preprompt", ""),
            "ui_dashboard": current_app.config["HOME_AI_DASHBOARD"],
        }
    )


@chatbot_bp.route("/preferences", methods=["PATCH"])
@login_required
def save_preferences():
    payload = request.get_json(silent=True) or {}
    prefs = {
        "selected_collections": _normalize_list(payload.get("selected_collections")),
        "selected_groups": _normalize_list(payload.get("selected_groups")),
        "user_preprompt": (payload.get("user_preprompt") or "").strip(),
    }
    session["chatbot_preferences"] = prefs
    session.modified = True
    return ok_response(message="Preferences saved.")


@chatbot_bp.route("/conversation/new", methods=["POST"])
@login_required
def new_conversation():
    convo_state = _load_conversations()
    conversation_id = _create_conversation(convo_state)
    _save_conversations(convo_state)
    return ok_response(
        {
            "conversation_id": conversation_id,
            "conversations": convo_state.get("items", []),
            "current_history": [],
        }
    )


@chatbot_bp.route("/conversation/select", methods=["PATCH"])
@login_required
def select_conversation():
    conversation_id = _normalize_id((request.get_json(silent=True) or {}).get("conversation_id"))
    if not conversation_id:
        return fail_response("Missing conversation_id", status_code=400)
    convo_state = _load_conversations()
    if not _has_conversation(convo_state, conversation_id):
        return fail_response("Conversation not found", status_code=404)
    convo_state["current_id"] = conversation_id
    _save_conversations(convo_state)
    return ok_response(
        {
            "conversation_id": conversation_id,
            "conversations": convo_state.get("items", []),
            "current_history": _get_conversation_history(convo_state, conversation_id),
        }
    )


@chatbot_bp.route("/conversation/delete", methods=["PATCH"])
@login_required
def delete_conversation():
    conversation_id = _normalize_id((request.get_json(silent=True) or {}).get("conversation_id"))
    if not conversation_id:
        return fail_response("Missing conversation_id", status_code=400)
    convo_state = _load_conversations()
    if not _has_conversation(convo_state, conversation_id):
        return fail_response("Conversation not found", status_code=404)

    items = [item for item in convo_state.get("items", []) if item.get("id") != conversation_id]
    history = dict(convo_state.get("history") or {})
    history.pop(conversation_id, None)
    convo_state["items"] = items
    convo_state["history"] = history
    if convo_state.get("current_id") == conversation_id:
        convo_state["current_id"] = items[0]["id"] if items else None
    _save_conversations(convo_state)
    active_id = convo_state.get("current_id")
    return ok_response(
        {
            "conversation_id": active_id,
            "conversations": convo_state.get("items", []),
            "current_history": _get_conversation_history(convo_state, active_id),
        }
    )


def _get_chat_client():
    client = current_app.extensions.get("home_ai_chat_client")
    if client is not None:
        return client

    app_root = Path(current_app.config["APP_ROOT"])
    comptes_dir = app_root / "GAR" / "comptes"
    if str(comptes_dir) not in sys.path:
        sys.path.insert(0, str(comptes_dir))

    from chat import ComptesChat

    client = ComptesChat(config_path=current_app.config["GAR_CONFIG_PATH"])
    current_app.extensions["home_ai_chat_client"] = client
    return client


def _list_collections() -> list[dict[str, Any]]:
    try:
        import chromadb

        config = load_gar_config()
        db_path = Path(config.get("vector_db", {}).get("persist_directory", "data/vector_db"))
        if not db_path.is_absolute():
            db_path = Path(current_app.config["APP_ROOT"]) / "GAR" / "comptes" / db_path
        chroma_client = chromadb.PersistentClient(path=str(db_path.absolute()))
        return [{"name": item.name, "count": item.count()} for item in chroma_client.list_collections()]
    except Exception:
        return []


def _collection_groups(collections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not collections:
        return []
    return [{"name": "local", "label": "Local knowledge", "count": len(collections), "collections": [c["name"] for c in collections]}]


def _collections_for_groups(groups: list[str]) -> list[str]:
    collections = _list_collections()
    if "local" in groups:
        return [c["name"] for c in collections]
    return []


def _context_and_sources(results: dict[str, Any], selected_collections: list[str]) -> tuple[str, list[dict[str, str]]]:
    docs = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    context_parts = []
    sources = []
    for index, doc in enumerate(docs):
        meta = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
        collection = meta.get("collection") or _default_collection_name()
        if selected_collections and collection not in selected_collections:
            continue
        distance = distances[index] if index < len(distances) else None
        file_name = str(meta.get("file") or meta.get("source") or "unknown")
        sheet = str(meta.get("sheet") or "")
        distance_text = f", Distance: {distance:.3f}" if isinstance(distance, (int, float)) else ""
        context_parts.append(f"Source: {file_name}{f' ({sheet})' if sheet else ''}{distance_text}\nContent: {doc}")
        sources.append({"label": file_name, "collection": collection, "download_url": ""})
    return "\n\n".join(context_parts), sources


def _preferences() -> dict[str, Any]:
    prefs = session.get("chatbot_preferences") or {}
    if not isinstance(prefs, dict):
        prefs = {}
    prefs.setdefault("selected_collections", [])
    prefs.setdefault("selected_groups", [])
    prefs.setdefault("user_preprompt", "")
    return prefs


def _load_conversations() -> dict[str, Any]:
    data = session.get("chatbot_conversations") or {}
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("items", [])
    data.setdefault("history", {})
    data.setdefault("current_id", None)
    return data


def _save_conversations(data: dict[str, Any]) -> None:
    _trim_conversations(data)
    session["chatbot_conversations"] = data
    session.modified = True


def _create_conversation(data: dict[str, Any]) -> str:
    convo_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    data.setdefault("items", []).insert(0, {"id": convo_id, "title": "New conversation", "created_at": now, "updated_at": now})
    data["current_id"] = convo_id
    data.setdefault("history", {})[convo_id] = []
    return convo_id


def _has_conversation(data: dict[str, Any], convo_id: str) -> bool:
    return any(item.get("id") == convo_id for item in data.get("items", []))


def _get_conversation_history(data: dict[str, Any], convo_id: str | None) -> list[dict[str, str]]:
    if not convo_id:
        return []
    history = (data.get("history") or {}).get(convo_id, [])
    return history if isinstance(history, list) else []


def _append_conversation_turn(data: dict[str, Any], convo_id: str, question: str, answer: str) -> None:
    history = data.setdefault("history", {}).setdefault(convo_id, [])
    history.append({"q": question, "a": answer})
    data["history"][convo_id] = history[-20:]
    for item in data.get("items", []):
        if item.get("id") == convo_id:
            if item.get("title") in (None, "", "New conversation"):
                item["title"] = question[:60] or "Conversation"
            item["updated_at"] = datetime.now(timezone.utc).isoformat()
            break
    data["items"] = _sort_conversations(data.get("items", []))


def _trim_conversations(data: dict[str, Any]) -> None:
    items = _sort_conversations(data.get("items", []))[:12]
    keep_ids = {item.get("id") for item in items if item.get("id")}
    data["items"] = items
    data["history"] = {k: v for k, v in (data.get("history") or {}).items() if k in keep_ids}
    if data.get("current_id") not in keep_ids:
        data["current_id"] = items[0]["id"] if items else None


def _sort_conversations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)


def _normalize_id(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _project_name() -> str:
    return _gar_config().get("project", {}).get("name", "Home AI")


def _default_collection_name() -> str:
    config = load_gar_config()
    tenant = config.get("project", {}).get("tenant", "home")
    return f"{tenant}_data"
