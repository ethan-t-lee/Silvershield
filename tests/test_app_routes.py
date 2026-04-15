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


def test_module_requires_pretest_before_entry(app_client):
    client, _, db_path = app_client
    _seed_user(db_path, username="alice")

    with client.session_transaction() as session:
        session["username"] = "alice"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO pre_survey (
                username, age, scammed, tech_level, device,
                gender_identity, education_level, employment_status, household_income,
                primary_language, country_region, prior_cyber_training, confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "alice", "25-34", "No", "Good", "Both",
                "Woman", "Bachelor degree", "Employed full-time", "75k-99k",
                "English", "United States", "Yes - once", 4,
            ),
        )
        conn.commit()

    response = client.get("/module1")

    assert response.status_code == 302
    assert "/module_assessment/desktop/pre" in response.headers["Location"]


def test_module_assessment_assigns_balanced_questions_and_allows_module_entry(app_client):
    client, app_module, db_path = app_client
    _seed_user(db_path, username="alice")

    with client.session_transaction() as session:
        session["username"] = "alice"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO pre_survey (
                username, age, scammed, tech_level, device,
                gender_identity, education_level, employment_status, household_income,
                primary_language, country_region, prior_cyber_training, confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "alice", "25-34", "No", "Good", "Both",
                "Woman", "Bachelor degree", "Employed full-time", "75k-99k",
                "English", "United States", "Yes - once", 4,
            ),
        )
        conn.commit()

    pre_page = client.get("/module_assessment/desktop/pre")
    assert pre_page.status_code == 200

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT variant
            FROM module_assessment_enrollments
            WHERE username = ? AND module_name = ?
            """,
            ("alice", "desktop"),
        )
        enrollment = cursor.fetchone()

        cursor.execute(
            """
            SELECT question_id, phase
            FROM module_assessment_assignments
            WHERE username = ? AND module_name = ?
            """,
            ("alice", "desktop"),
        )
        assignments = cursor.fetchall()

    assert enrollment is not None
    assert enrollment[0] in {"A", "B"}
    assert len(assignments) == 10
    pre_ids = [row[0] for row in assignments if row[1] == "pre"]
    post_ids = [row[0] for row in assignments if row[1] == "post"]
    assert len(pre_ids) == 5
    assert len(post_ids) == 5
    assert set(pre_ids).isdisjoint(set(post_ids))

    question_map = {q["id"]: q for q in app_module.MODULE_ASSESSMENT_QUESTION_BANK}
    submit_data = {f"q_{qid}": question_map[qid]["correct"] for qid in pre_ids}

    submit_response = client.post("/module_assessment/desktop/pre", data=submit_data)
    assert submit_response.status_code == 302
    assert submit_response.headers["Location"].endswith("/module1")

    module_response = client.get("/module1")
    assert module_response.status_code == 200


def test_module_posttest_requires_pretest_and_training_completion(app_client):
    client, app_module, db_path = app_client
    _seed_user(db_path, username="alice")

    with client.session_transaction() as session:
        session["username"] = "alice"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO pre_survey (
                username, age, scammed, tech_level, device,
                gender_identity, education_level, employment_status, household_income,
                primary_language, country_region, prior_cyber_training, confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "alice", "25-34", "No", "Good", "Both",
                "Woman", "Bachelor degree", "Employed full-time", "75k-99k",
                "English", "United States", "Yes - once", 4,
            ),
        )
        conn.commit()

    blocked_without_pre = client.get("/module_assessment/desktop/post")
    assert blocked_without_pre.status_code == 302
    assert "/module_assessment/desktop/pre" in blocked_without_pre.headers["Location"]

    client.get("/module_assessment/desktop/pre")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT question_id
            FROM module_assessment_assignments
            WHERE username = ? AND module_name = ? AND phase = ?
            """,
            ("alice", "desktop", "pre"),
        )
        pre_ids = [row[0] for row in cursor.fetchall()]

    question_map = {
        q["id"]: q
        for q in app_module.MODULE_ASSESSMENT_QUESTION_BANKS["desktop"]
    }
    submit_data = {f"q_{qid}": question_map[qid]["correct"] for qid in pre_ids}
    client.post("/module_assessment/desktop/pre", data=submit_data)

    blocked_without_training = client.get("/module_assessment/desktop/post")
    assert blocked_without_training.status_code == 302
    assert blocked_without_training.headers["Location"].endswith("/module1")


def test_module_back_button_routes_to_posttest_after_training_completion(app_client):
    client, app_module, db_path = app_client
    _seed_user(db_path, username="alice")

    with client.session_transaction() as session:
        session["username"] = "alice"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO pre_survey (
                username, age, scammed, tech_level, device,
                gender_identity, education_level, employment_status, household_income,
                primary_language, country_region, prior_cyber_training, confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "alice", "25-34", "No", "Good", "Both",
                "Woman", "Bachelor degree", "Employed full-time", "75k-99k",
                "English", "United States", "Yes - once", 4,
            ),
        )
        conn.commit()

    client.get("/module_assessment/desktop/pre")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT question_id
            FROM module_assessment_assignments
            WHERE username = ? AND module_name = ? AND phase = ?
            """,
            ("alice", "desktop", "pre"),
        )
        pre_ids = [row[0] for row in cursor.fetchall()]

    question_map = {
        q["id"]: q
        for q in app_module.MODULE_ASSESSMENT_QUESTION_BANKS["desktop"]
    }
    submit_data = {f"q_{qid}": question_map[qid]["correct"] for qid in pre_ids}
    client.post("/module_assessment/desktop/pre", data=submit_data)

    incomplete_response = client.get("/module1")
    incomplete_body = incomplete_response.get_data(as_text=True)
    assert 'class="module-back-link" href="/dashboard"' in incomplete_body

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO module_progress (username, module_name, scenarios_completed, total_scenarios, last_accessed)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ("alice", "email_desktop", 5, 5),
        )
        conn.execute(
            """
            INSERT INTO module_progress (username, module_name, scenarios_completed, total_scenarios, last_accessed)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ("alice", "internet_desktop", 5, 5),
        )
        conn.commit()

    complete_response = client.get("/module1")
    complete_body = complete_response.get_data(as_text=True)
    assert 'class="module-back-link" href="/module_assessment/desktop/post"' in complete_body


def test_dashboard_redirects_to_pre_survey_until_complete(app_client):
    client, _, db_path = app_client
    _seed_user(db_path, username="alice")

    with client.session_transaction() as session:
        session["username"] = "alice"

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/pre_survey")


def test_dashboard_access_after_pre_survey_complete(app_client):
    client, _, db_path = app_client
    _seed_user(db_path, username="alice")

    with client.session_transaction() as session:
        session["username"] = "alice"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO pre_survey (
                username, age, scammed, tech_level, device,
                gender_identity, education_level, employment_status, household_income,
                primary_language, country_region, prior_cyber_training, confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "alice", "25-34", "No", "Good", "Both",
                "Woman", "Bachelor degree", "Employed full-time", "75k-99k",
                "English", "United States", "Yes - once", 4,
            ),
        )
        conn.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200


def test_pre_survey_saves_amplify_questions(app_client):
    client, _, db_path = app_client
    _seed_user(db_path, username="alice")

    with client.session_transaction() as session:
        session["username"] = "alice"

    demographics_response = client.post(
        "/pre_survey_demographics",
        data={
            "age": "25-34",
            "scammed": "No",
            "tech_level": "Good",
            "device": "Both",
            "gender_identity": "Woman",
            "education_level": "Bachelor degree",
            "employment_status": "Employed full-time",
            "household_income": "75k-99k",
            "primary_language": "English",
            "country_region": "United States",
            "prior_cyber_training": "Yes - once",
            "confidence": "4",
        },
    )

    assert demographics_response.status_code == 302
    assert demographics_response.headers["Location"].endswith("/pre_survey")

    response = client.post(
        "/pre_survey",
        data={
            "smishing_familiarity": "Familiar",
            "security_software_usage": "Yes",
            "unknown_link_click_frequency": "Rarely",
            "sms_phishing_awareness": "Aware",
            "sms_phishing_victim": "No",
            "familiar_7726": "No",
            "suspected_sms_action": "Ignore or delete the message",
            "sms_phishing_definition": "Sending fake text messages to steal personal information",
            "cyber_training_history": "Yes",
            "cyber_training_format": "Cyber Training",
            "cyber_training_timing": "Within two years",
            "training_covered_sms_phishing": "Yes",
            "training_usefulness": "Very useful",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
             SELECT age, device,
                 smishing_familiarity, security_software_usage, unknown_link_click_frequency,
                 sms_phishing_awareness, sms_phishing_victim, familiar_7726,
                 suspected_sms_action, sms_phishing_definition, cyber_training_history,
                 cyber_training_format, cyber_training_timing,
                 training_covered_sms_phishing, training_usefulness
            FROM pre_survey
            WHERE username = ?
            """,
            ("alice",),
        )
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == "25-34"
    assert row[1] == "Both"
    assert row[2] == "Familiar"
    assert row[3] == "Yes"
    assert row[4] == "Rarely"
    assert row[5] == "Aware"
    assert row[6] == "No"
    assert row[7] == "No"
    assert row[8] == "Ignore or delete the message"
    assert row[9] == "Sending fake text messages to steal personal information"
    assert row[10] == "Yes"
    assert row[11] == "Cyber Training"
    assert row[12] == "Within two years"
    assert row[13] == "Yes"
    assert row[14] == "Very useful"


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
