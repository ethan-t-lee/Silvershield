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
