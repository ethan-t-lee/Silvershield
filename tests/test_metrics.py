import sqlite3

import pytest

import database
import metrics


def test_log_scenario_attempt_updates_performance_and_indicators(monkeypatch, tmp_path):
    db_path = str(tmp_path / "metrics_test.db")
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(metrics, "DB_PATH", db_path)

    database.init_database()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (username, email, phone, address, password_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("alice", "alice@example.com", "1234567890", "123 Main St", "hashed"),
        )
        conn.commit()

    metrics.log_scenario_attempt(
        username="alice",
        scenario_type="email",
        platform="desktop",
        user_choice="scam",
        correct_answer="scam",
        is_correct=True,
        difficulty_level=2,
        duration_seconds=30,
        indicators_found=["urgent language", "suspicious link"],
    )

    performance = metrics.get_user_performance("alice")
    assert performance["success"] is True
    assert performance["data"][0]["scenario_type"] == "email"
    assert performance["data"][0]["total_attempts"] == 1
    assert performance["data"][0]["correct_attempts"] == 1
    assert performance["data"][0]["success_rate"] == pytest.approx(100.0)
    assert performance["data"][0]["critical_indicators_found"] == 2


def test_update_module_progress_tracks_completion(monkeypatch, tmp_path):
    db_path = str(tmp_path / "module_progress_test.db")
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(metrics, "DB_PATH", db_path)

    database.init_database()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (username, email, phone, address, password_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("bob", "bob@example.com", "0987654321", "456 Oak Ave", "hashed"),
        )
        conn.commit()

    metrics.update_module_progress("bob", "module1")
    result = metrics.get_module_progress("bob")

    assert result["success"] is True
    assert result["modules"][0]["module_name"] == "module1"
    assert result["modules"][0]["completed"] == 1
    assert result["modules"][0]["total"] == 5


def test_update_module_progress_caps_at_total(monkeypatch, tmp_path):
    db_path = str(tmp_path / "module_progress_cap_test.db")
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(metrics, "DB_PATH", db_path)

    database.init_database()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (username, email, phone, address, password_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("carol", "carol@example.com", "1112223333", "789 Pine Rd", "hashed"),
        )
        conn.commit()

    for _ in range(10):
        metrics.update_module_progress("carol", "module1")

    result = metrics.get_module_progress("carol")

    assert result["success"] is True
    assert result["modules"][0]["completed"] == 5
    assert result["modules"][0]["total"] == 5
    assert result["modules"][0]["completion_percentage"] == 100.0
