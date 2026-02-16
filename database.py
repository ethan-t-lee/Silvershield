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
connect.commit()
connect.close()
