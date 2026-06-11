from __future__ import annotations

from werkzeug.security import generate_password_hash

from home_ai import create_app


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    APP_ROOT = "."
    GAR_CONFIG_PATH = "GAR/comptes/config.yml"
    HOME_AI_ADMIN_USER = "admin"
    HOME_AI_ADMIN_PASSWORD_HASH = generate_password_hash("admin")
    HOME_AI_DASHBOARD = {
        "version": 1,
        "grid": {"columns": 6, "rows": 10},
        "modules": {"chat": {"type": "chat", "enabled": True, "placement": {"col": 1, "row": 1, "colspan": 6, "rowspan": 8}}},
    }


class FakeChatClient:
    def query_vector_db(self, question, n_results=5):
        return {
            "documents": [[f"Relevant local context for {question}"]],
            "metadatas": [[{"file": "sample.ods", "sheet": "Sheet1", "collection": "comptes_data"}]],
            "distances": [[0.12]],
        }

    def generate_answer(self, question, context):
        return f"Answered: {question}"


def login(client):
    return client.post("/login", data={"username": "admin", "password": "admin"})


def test_login_required_for_chat():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/chatbot/chat")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_login_and_chat_page():
    app = create_app(TestConfig)
    client = app.test_client()

    response = login(client)
    assert response.status_code == 302

    page = client.get("/chatbot/chat")
    assert page.status_code == 200
    assert b"Chatbot for comptes" in page.data
    assert b"Ingestors" in page.data


def test_chat_endpoint_uses_cached_client():
    app = create_app(TestConfig)
    client = app.test_client()
    login(client)
    app.extensions["home_ai_chat_client"] = FakeChatClient()

    response = client.post("/chatbot/chat", json={"message": "hello"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["response"] == "Answered: hello"
    assert payload["data"]["sources"][0]["label"] == "sample.ods"


def test_ingestors_page_lists_configured_sources():
    app = create_app(TestConfig)
    client = app.test_client()
    login(client)

    page = client.get("/manage/ingestors")

    assert page.status_code == 200
    assert b"Ingestors" in page.data
    assert b"/home/thierry/Documents/Private/Comptes" in page.data
    assert b"data/vector_db" in page.data
