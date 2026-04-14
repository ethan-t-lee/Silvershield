import json
import sqlite3


def _seed_user(db_path, username="alice", password_hash="hashed"):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (username, email, phone, address, password_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, f"{username}@example.com", "1234567890", "123 Main St", password_hash),
        )
        conn.commit()


def test_home_page_loads(app_client):
    client, _, _ = app_client
    response = client.get("/")
    assert response.status_code == 200


def test_user_performance_requires_login(app_client):
    client, _, _ = app_client
    response = client.get("/api/user_performance")

    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_register_and_login_flow(app_client):
    client, _, _ = app_client

    register_response = client.post(
        "/register",
        data={
            "username": "alice",
            "password": "StrongPass123!",
            "email": "alice@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
        },
    )

    assert register_response.status_code == 200
    assert register_response.get_json()["success"] is True

    login_response = client.post(
        "/login",
        data={"username": "alice", "password": "StrongPass123!"},
    )

    login_payload = login_response.get_json()
    assert login_response.status_code == 200
    assert login_payload["success"] is True
    assert login_payload["otp_sent"] is True


def test_seeded_test_user_bypasses_otp(app_client):
    client, app_module, _ = app_client

    send_otp_calls = []
    app_module.send_otp = lambda phone: send_otp_calls.append(phone)

    login_response = client.post(
        "/login",
        data={
            "username": app_module.TEST_USER_USERNAME,
            "password": "SilverShieldTest!1",
        },
    )

    login_payload = login_response.get_json()
    assert login_response.status_code == 200
    assert login_payload["success"] is True
    assert login_payload["twilio_bypassed"] is True
    assert login_payload["otp_sent"] is False
    assert send_otp_calls == []


def test_phone_roleplay_session_requires_login(app_client):
    client, _, _ = app_client
    response = client.post(
        "/phone-roleplay/start-session",
        json={"scenario_type": "bank_fraud", "difficulty_level": 2},
    )

    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_phone_roleplay_session_can_start_for_logged_in_user(app_client):
    client, _, db_path = app_client
    _seed_user(db_path, username="alice")

    with client.session_transaction() as session:
        session["username"] = "alice"

    response = client.post(
        "/phone-roleplay/start-session",
        json={"scenario_type": "bank_fraud", "difficulty_level": 2},
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["session_id"] > 0


def test_generate_sites_list_returns_results(app_client, monkeypatch):
    client, app_module, _ = app_client

    class FakeGroqResponse:
        def __init__(self, site_type):
            self.site_type = site_type

        def json(self):
            payload = {
                "title": f"{self.site_type.title()} Example",
                "url": f"https://{self.site_type}.example.com",
                "description": "Example description",
                "site_type": self.site_type,
            }
            return {"choices": [{"message": {"content": json.dumps(payload)}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        prompt = json["messages"][0]["content"]
        site_type = "phishing" if "PHISHING" in prompt else "legit"
        return FakeGroqResponse(site_type)

    monkeypatch.setattr(app_module.requests, "post", fake_post)

    response = client.post("/api/generate_sites", json={"mode": "list", "query": "bank login"})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["query"] == "bank login"
    assert len(payload["results"]) == 5


def test_generate_web_search_returns_results(app_client, monkeypatch):
    client, app_module, _ = app_client

    class FakeGroqResponse:
        def __init__(self, content):
            self.content = content

        def json(self):
            return {"choices": [{"message": {"content": self.content}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        prompt = json["messages"][0]["content"]
        if "top-level keys: ads, results, pagination, clues" in prompt:
            payload = {
                "ads": [
                    {"title": "Official Bank Help", "url": "https://bank.example.com", "snippet": "Official support.", "site_type": "legit"},
                    {"title": "Verify Bank Login", "url": "https://bank-login-check.com", "snippet": "Urgent account action.", "site_type": "phishing"},
                ],
                "results": [
                    {"title": f"Result {idx}", "url": f"https://example{idx}.com", "snippet": "Example snippet", "site_type": "legit" if idx % 2 == 0 else "phishing"}
                    for idx in range(6)
                ],
                "pagination": {"next_page_label": "Next >", "page_number": 1},
                "clues": []
            }
            return FakeGroqResponse(json_module.dumps(payload))
        return FakeGroqResponse("<div><h2>Example Site</h2></div>")

    import json as json_module
    monkeypatch.setattr(app_module.requests, "post", fake_post)

    response = client.post("/generate-web", json={"mode": "search", "query": "bank login"})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["query"] == "bank login"
    assert len(payload["web"]["ads"]) == 2
    assert len(payload["web"]["results"]) == 6


def test_internet_pages_fall_back_when_model_refuses(app_client, monkeypatch):
    client, app_module, _ = app_client
    refusal = "I cannot generate content that could be used to phishing victims. Is there something else I can help you with?"

    class RefusalResponse:
        def json(self):
            return {"choices": [{"message": {"content": refusal}}]}

    monkeypatch.setattr(app_module.requests, "post", lambda *args, **kwargs: RefusalResponse())

    desktop_response = client.post(
        "/api/generate_sites",
        json={
            "mode": "open",
            "query": "bank login",
            "title": "Bank Help Center",
            "url": "https://bank.example.com",
            "site_type": "phishing",
        },
    )
    mobile_response = client.post(
        "/generate-web",
        json={
            "mode": "open",
            "query": "bank login",
            "title": "Bank Help Center",
            "url": "https://bank.example.com",
            "site_type": "phishing",
        },
    )

    desktop_payload = desktop_response.get_json()
    mobile_payload = mobile_response.get_json()

    assert desktop_response.status_code == 200
    assert refusal not in desktop_payload["html"]
    assert "confirm" in desktop_payload["html"].lower() or "review" in desktop_payload["html"].lower()

    assert mobile_response.status_code == 200
    assert refusal not in mobile_payload["html"]
    assert "confirm" in mobile_payload["html"].lower() or "review" in mobile_payload["html"].lower()


def test_content_generators_fall_back_when_groq_returns_no_choices(app_client, monkeypatch):
    client, app_module, _ = app_client

    class EmptyGroqResponse:
        def json(self):
            return {}

    monkeypatch.setattr(app_module.requests, "post", lambda *args, **kwargs: EmptyGroqResponse())

    email_response = client.post("/generate-email", json={"platform": "mobile"})
    sms_response = client.post("/generate-sms", json={"theme": "bank login"})
    call_response = client.post("/generate-call", json={"theme": "bank support"})

    email_payload = email_response.get_json()
    sms_payload = sms_response.get_json()
    call_payload = call_response.get_json()

    assert email_response.status_code == 200
    assert email_payload["success"] is True
    assert email_payload["email"]

    assert sms_response.status_code == 200
    assert sms_payload["success"] is True
    assert sms_payload["sms"]["text"]

    assert call_response.status_code == 200
    assert call_payload["success"] is True
    assert call_payload["call"]["transcript"]
