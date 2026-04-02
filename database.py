import sqlite3

DB_PATH = 'silvershieldDatabase.db'


def _column_names(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def _table_exists(cursor, table_name):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def _migrate_scenario_attempts(cursor):
    if not _table_exists(cursor, 'scenario_attempts'):
        cursor.execute('''CREATE TABLE IF NOT EXISTS scenario_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        scenario_type TEXT NOT NULL,
                        scenario_platform TEXT NOT NULL,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        duration_seconds INTEGER,
                        user_choice TEXT NOT NULL,
                        correct_answer TEXT NOT NULL,
                        is_correct BOOLEAN NOT NULL,
                        difficulty_level INTEGER NOT NULL,
                        ai_feedback TEXT,
                        message TEXT,
                        FOREIGN KEY(username) REFERENCES users(username))
        ''')
        return

    scenario_attempt_cols = _column_names(cursor, 'scenario_attempts')
    needs_rebuild = (
        'attempt_number' in scenario_attempt_cols or
        'critical_indicators_identified' in scenario_attempt_cols
    )

    if needs_rebuild:
        cursor.execute('PRAGMA foreign_keys=OFF')
        cursor.execute('''CREATE TABLE IF NOT EXISTS scenario_attempts_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        scenario_type TEXT NOT NULL,
                        scenario_platform TEXT NOT NULL,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        duration_seconds INTEGER,
                        user_choice TEXT NOT NULL,
                        correct_answer TEXT NOT NULL,
                        is_correct BOOLEAN NOT NULL,
                        difficulty_level INTEGER NOT NULL,
                        ai_feedback TEXT,
                        message TEXT,
                        FOREIGN KEY(username) REFERENCES users(username))
        ''')

        message_select = 'message' if 'message' in scenario_attempt_cols else 'NULL AS message'

        cursor.execute(f'''INSERT INTO scenario_attempts_new (
                        id, username, scenario_type, scenario_platform,
                        start_time, end_time, duration_seconds,
                        user_choice, correct_answer, is_correct,
                        difficulty_level, ai_feedback, message)
                        SELECT id, username, scenario_type, scenario_platform,
                        start_time, end_time, duration_seconds,
                        user_choice, correct_answer, is_correct,
                        difficulty_level, ai_feedback, {message_select}
                        FROM scenario_attempts
        ''')

        cursor.execute('DROP TABLE scenario_attempts')
        cursor.execute('ALTER TABLE scenario_attempts_new RENAME TO scenario_attempts')
        cursor.execute('PRAGMA foreign_keys=ON')
        scenario_attempt_cols = _column_names(cursor, 'scenario_attempts')

    if 'message' not in scenario_attempt_cols:
        cursor.execute('ALTER TABLE scenario_attempts ADD COLUMN message TEXT')


def init_database():
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    address TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    difficulty_email_desktop INTEGER DEFAULT 1,
                    difficulty_internet_desktop INTEGER DEFAULT 1,
                    difficulty_email_mobile INTEGER DEFAULT 1,
                    difficulty_sms_mobile INTEGER DEFAULT 1,
                    difficulty_call_mobile INTEGER DEFAULT 1,
                    difficulty_web_mobile INTEGER DEFAULT 1)
    ''')

    _migrate_scenario_attempts(cursor)

    cursor.execute('''CREATE TABLE IF NOT EXISTS pre_survey (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    age TEXT,
                    scammed TEXT,
                    tech_level TEXT,
                    device TEXT,
                    confidence INTEGER,
                    completed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(username) REFERENCES users(username))
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS post_survey (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    confidence_rating INTEGER,
                    perceived_usefulness INTEGER,
                    behavior_change TEXT,
                    recommendation_likelihood INTEGER,
                    learning_rating INTEGER,
                    completed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(username) REFERENCES users(username))
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS performance_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    scenario_type TEXT NOT NULL,
                    total_attempts INTEGER NOT NULL DEFAULT 0,
                    correct_attempts INTEGER NOT NULL DEFAULT 0,
                    success_rate REAL NOT NULL DEFAULT 0,
                    average_duration_seconds REAL NOT NULL DEFAULT 0,
                    total_indicators_identified INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(username, scenario_type),
                    FOREIGN KEY(username) REFERENCES users(username))
    ''')

    performance_cols = _column_names(cursor, 'performance_summary')
    if 'total_indicators_identified' not in performance_cols:
        cursor.execute(
            'ALTER TABLE performance_summary ADD COLUMN total_indicators_identified INTEGER NOT NULL DEFAULT 0'
        )

    cursor.execute('''CREATE TABLE IF NOT EXISTS module_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    module_name TEXT NOT NULL,
                    scenarios_completed INTEGER NOT NULL DEFAULT 0,
                    total_scenarios INTEGER NOT NULL DEFAULT 5,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(username, module_name),
                    FOREIGN KEY(username) REFERENCES users(username))
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS critical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    scenario_attempt_id INTEGER NOT NULL,
                    scenario_type TEXT NOT NULL,
                    indicator_name TEXT NOT NULL,
                    identified BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(username) REFERENCES users(username),
                    FOREIGN KEY(scenario_attempt_id) REFERENCES scenario_attempts(id))
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS phone_roleplay_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    scenario_type TEXT NOT NULL,
                    difficulty_level INTEGER DEFAULT 1,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    total_time_seconds REAL,
                    final_outcome TEXT,
                    score INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0)
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS phone_roleplay_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_value TEXT,
                    timestamp TEXT NOT NULL,
                    time_offset_seconds REAL,
                    FOREIGN KEY(session_id) REFERENCES phone_roleplay_sessions(id))
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS phone_roleplay_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    attempt_count INTEGER DEFAULT 0,
                    critical_indicators_found INTEGER DEFAULT 0,
                    critical_indicators_total INTEGER DEFAULT 0,
                    used_hint INTEGER DEFAULT 0,
                    behavior_pattern TEXT,
                    feedback_shown TEXT,
                    FOREIGN KEY(session_id) REFERENCES phone_roleplay_sessions(id))
    ''')
    
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_attempts_username_time
                    ON scenario_attempts(username, start_time DESC)
    ''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_indicators_attempt
                    ON critical_indicators(scenario_attempt_id)
    ''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_module_progress_user
                    ON module_progress(username, last_accessed DESC)
    ''')

    connect.commit()
    connect.close()


if __name__ == '__main__':
    init_database()
