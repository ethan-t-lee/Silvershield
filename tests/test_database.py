import sqlite3

import database


def test_init_database_creates_expected_tables(monkeypatch, tmp_path):
    db_path = str(tmp_path / "database_test.db")
    monkeypatch.setattr(database, "DB_PATH", db_path)

    database.init_database()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "users",
        "pre_survey",
        "post_survey",
        "scenario_attempts",
        "performance_summary",
        "module_progress",
        "critical_indicators",
        "phone_roleplay_sessions",
        "phone_roleplay_events",
        "phone_roleplay_results",
    }

    assert expected_tables.issubset(tables)
