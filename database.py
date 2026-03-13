import sqlite3

connect = sqlite3.connect('silvershieldDatabase.db')
cursor = connect.cursor()

# Remove legacy scenario_attempts columns if they still exist.
cursor.execute("PRAGMA table_info(scenario_attempts)")
scenario_attempt_cols = [row[1] for row in cursor.fetchall()]

if "attempt_number" in scenario_attempt_cols or "critical_indicators_identified" in scenario_attempt_cols:
    cursor.execute("PRAGMA foreign_keys=OFF")

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

    message_select = "message" if "message" in scenario_attempt_cols else "NULL AS message"

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
    cursor.execute("PRAGMA foreign_keys=ON")

# Add message column to scenario_attempts if not present
try:
    cursor.execute('ALTER TABLE scenario_attempts ADD COLUMN message TEXT')
except:
    pass  # Column already exists

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
connect.commit()
connect.close()
