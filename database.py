import sqlite3

connect = sqlite3.connect('silvershieldDatabase.db')
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
connect.commit()
connect.close()
