import importlib
import sqlite3

import pytest

import database
import metrics
import user_login


@pytest.fixture
def test_db_path(tmp_path):
    return str(tmp_path / "test_silvershield.db")


@pytest.fixture
def app_client(monkeypatch, test_db_path):
    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(metrics, "DB_PATH", test_db_path)

    def _connect_to_test_db():
        conn = sqlite3.connect(test_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(user_login, "connecting_to_database", _connect_to_test_db)
    database.init_database()

    import app as app_module
    app_module = importlib.reload(app_module)

    monkeypatch.setattr(app_module, "DB_PATH", test_db_path)
    monkeypatch.setattr(app_module, "send_otp", lambda phone: None)
    monkeypatch.setattr(app_module, "verify_otp", lambda phone, code: code == "123456")

    real_connect = sqlite3.connect

    def redirected_connect(path, *args, **kwargs):
        if path == "silvershieldDatabase.db":
            path = test_db_path
        return real_connect(path, *args, **kwargs)

    monkeypatch.setattr(app_module.sqlite3, "connect", redirected_connect)
    monkeypatch.setattr(database.sqlite3, "connect", redirected_connect)
    monkeypatch.setattr(user_login.sqlite3, "connect", redirected_connect)
    monkeypatch.setattr(metrics.sqlite3, "connect", redirected_connect)

    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")

    with app_module.app.test_client() as client:
        yield client, app_module, test_db_path
