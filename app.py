from flask import Flask, render_template, request, jsonify, flash, session, redirect, url_for
import os
import sqlite3
from dotenv import load_dotenv
import requests
from database import init_database
from user_login import user_registration, verifying_login
from TWOFA import send_otp, verify_otp
from flask_babel import Babel, gettext, get_locale, _
import json
from datetime import datetime, timezone
import time
from metrics import (log_scenario_attempt, log_critical_indicators, 
                     update_module_progress, get_user_performance, get_module_progress, 
                     get_attempt_history, get_survey_comparison, get_learning_metrics)

load_dotenv()

# Read GROQ key from environment (.env)
GROQ_KEY = os.getenv("GROQ_KEY")

# Database path
DB_PATH = "silvershieldDatabase.db"

app = Flask(__name__)
app.secret_key = "SECRET KEY"
init_database()

# Babel locale selector
def select_locale():
    return session.get('lang', request.accept_languages.best_match(['en', 'es', 'zh']))


def get_llm_output_language():
    lang = session.get('lang', request.accept_languages.best_match(['en', 'es', 'zh'])) or 'en'
    lang = str(lang).lower()
    if lang.startswith('es'):
        return "Spanish"
    if lang.startswith('zh'):
        return "Chinese"
    return "English"

babel = Babel(app, locale_selector=select_locale)


@app.context_processor
def inject_template_helpers():
    return {"get_locale": get_locale}

# Homepage route

# Language switch route
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ('en', 'es', 'zh'):
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

# Register multimodal blueprint (text-to-speech) if available
try:
    from multimodal import multimodal_bp
    app.register_blueprint(multimodal_bp)
except Exception as _err:
    print('Multimodal blueprint not registered:', _err)

################################
# Loading difficulty from
#       the database
################################
def get_difficulty(category):
    username = session.get('username')
    if not username:
        return 1

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT {category} FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()

    return row[0] if row else 1

################################
# Saving difficulty to the
#        database
################################
def set_difficulty(category, level):
    # 1 - easy, 2 - medium, 3 - hard, 4 - very hard
    level = max(1, min(4, level))

    username = session.get('username')
    if not username:
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE users SET {category} = ? WHERE username = ?', (level, username))
        conn.commit()

################################
#         Page routes
################################
# Pre Survey #####################

@app.route('/')
def home():
    # Use the same function as Babel
    current_lang = session.get('lang', request.accept_languages.best_match(['en', 'es', 'zh']))
    return render_template('homePage.html', current_lang=current_lang)


@app.route('/pre_survey', methods=['GET', 'POST'])
def pre_survey():
    username = session.get('username')
    if not username:
        return redirect('/login')

    # If already completed, skip
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pre_survey WHERE username = ?", (username,))
        if cur.fetchone():
            return redirect('/dashboard')

    # POST block is inside function (indented)
    if request.method == 'POST':
        age = request.form.get('age')
        scammed = request.form.get('scammed')
        tech_level = request.form.get('tech_level')
        device = request.form.get('device')
        confidence = request.form.get('confidence')

        if not age or not scammed or not tech_level or not device or not confidence:
            flash("Please answer all questions.")
            return render_template("preSurvey.html")

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO pre_survey (username, age, scammed, tech_level, device, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    age=excluded.age,
                    scammed=excluded.scammed,
                    tech_level=excluded.tech_level,
                    device=excluded.device,
                    confidence=excluded.confidence,
                    completed_timestamp=CURRENT_TIMESTAMP
            """, (username, age, scammed, tech_level, device, int(confidence)))
            conn.commit()

        return redirect('/dashboard')

    # GET loads the form
    return render_template("preSurvey.html")





@app.route('/login', methods=['GET'])
def login():
    return render_template("loginPage.html")


@app.route('/account_creation')
def account_creation():
    return render_template("accountCreation.html")


@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        return redirect('/login')

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pre_survey WHERE username = ?", (username,))
        done = cur.fetchone() is not None

    if not done:
        return redirect('/pre_survey')

    return render_template("dashboard.html")

@app.route('/post_survey', methods=['GET', 'POST'])
def post_survey():
    username = session.get('username')
    if not username:
        return redirect('/login')

    if request.method == 'POST':
        confidence_rating = request.form.get('confidence_rating')
        perceived_usefulness = request.form.get('perceived_usefulness')
        behavior_change = request.form.get('behavior_change')
        recommendation_likelihood = request.form.get('recommendation_likelihood')
        learning_rating = request.form.get('learning_rating')

        if not all([confidence_rating, perceived_usefulness, behavior_change,
                    recommendation_likelihood, learning_rating]):
            flash("Please answer all questions.")
            return render_template("postSurvey.html")

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO post_survey (username, confidence_rating, perceived_usefulness,
                    behavior_change, recommendation_likelihood, learning_rating)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username,
                  int(confidence_rating),
                  int(perceived_usefulness),
                  behavior_change,
                  int(recommendation_likelihood),
                  int(learning_rating)))
            conn.commit()

        return redirect('/dashboard')

    return render_template("postSurvey.html")


@app.route("/reset_presurvey")
def reset_presurvey():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS pre_survey")
        conn.commit()
    return "pre_survey table dropped. Restart the server now."


@app.route('/module1')
def module1():
    return render_template("desktopPage.html")


@app.route('/module2')
def module2():
    return render_template("MobilePage.html")

@app.route('/phone_roleplay')
def phone_roleplay():
    return render_template("phoneRoleplay.html")


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/login')


################################
# Assessment & Analytics Endpoints
################################
@app.route('/api/user_performance', methods=['GET'])
def api_user_performance():
    """
    Get overall performance summary for a user across all scenario types.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    result = get_user_performance(username)
    if not result['success']:
        return jsonify(result), 500
    return jsonify(result)


@app.route('/api/module_progress', methods=['GET'])
def api_module_progress():
    """
    Get module completion progress for a user.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    result = get_module_progress(username)
    if not result['success']:
        return jsonify(result), 500
    return jsonify(result)


@app.route('/api/attempt_history', methods=['GET'])
def api_attempt_history():
    """
    Get detailed history of scenario attempts for a user.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    scenario_type = request.args.get('type')
    limit = request.args.get('limit', 20, type=int)

    result = get_attempt_history(username, scenario_type, limit)
    if not result['success']:
        return jsonify(result), 500
    return jsonify(result)


@app.route('/api/survey_comparison', methods=['GET'])
def api_survey_comparison():
    """
    Compare pre-survey and post-survey results for behavioral change assessment.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    result = get_survey_comparison(username)
    if not result['success']:
        return jsonify(result), 500
    return jsonify(result)


@app.route('/api/learning_metrics', methods=['GET'])
def api_learning_metrics():
    """
    Comprehensive learning metrics including time spent, difficulty progression,
    and identified critical indicators.
    """
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    result = get_learning_metrics(username)
    if not result['success']:
        return jsonify(result), 500
    return jsonify(result)


@app.route('/save_progress')
def save_progress():
    flash('Progress saved successfully!', 'success')
    return render_template("dashboard.html")

################################
#      Registration route
################################
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']

    success, message = user_registration(username, password, email, phone, address)
    return jsonify(success=success, message=message)


################################
#      Logging in route
################################
@app.route('/login', methods=['POST'])
def login_post():
    usernameorEmail = request.form['username'].strip()
    password = request.form['password'].strip()

    valid, phone = verifying_login(usernameorEmail, password)

    if not valid:
        return jsonify({"success": False, "message": "Invalid username or password"})

    if not phone.startswith("+"):
        phone = "+1" + phone

    # Storing logged in user for session
    session["username"] = usernameorEmail

    try:
        send_otp(phone)
        return jsonify({"success": True, "otp_sent": True, "phone": phone})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

################################
#       Validation route
################################
@app.route('/check_username')
def check_username():
    username = request.args.get("username")

    if not username:
        return jsonify({"exists": False})

    with sqlite3.connect("silvershieldDatabase.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None

    return jsonify({"exists": exists})

@app.route('/check_email')
def check_email():
    email = request.args.get("email")

    if not email:
        return jsonify({"exists": False})

    with sqlite3.connect("silvershieldDatabase.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        exists = cursor.fetchone() is not None

    return jsonify({"exists": exists})

@app.route('/send_otp', methods=['POST'])
def send_otp_route():
    phone = request.form['phone']

    if not phone.startswith("+"):
        phone = "+1" + phone

    try:
        send_otp(phone)
        return jsonify({"success": True, "message": "OTP sent"})
    except Exception as e:
        print("Error sending OTP", e)
        return jsonify({"success": False, "message": str(e)})

@app.route('/verify_otp', methods=['POST'])
def verify_otp_route():
    phone = request.form['phone']
    code = request.form['code']

    if not phone.startswith("+"):
        phone = "+1" + phone

    try:
        if verify_otp(phone, code):
            return jsonify({"success": True, "message": "OTP verified"})
        else:
            return jsonify({"success": False, "message": "OTP not verified"})
    except Exception as e:
        print("Error verifying OTP", e)
        return jsonify({"success": False, "message": str(e)})

##############################
# Phone Roleplay AI
##############################
@app.route("/generate-roleplay-line", methods=["POST"])
def generate_roleplay_line():
    data = request.get_json() or {}

    scenario_type = data.get("scenario_type")
    prompt_key = data.get("prompt_key")
    difficulty = int(data.get("difficulty", 1))

    print("roleplay line request:", scenario_type, prompt_key, difficulty)

    if not scenario_type or not prompt_key:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    difficulty_text = {
        1: "Make the scam obvious and easy for beginners to detect.",
        2: "Make the scam somewhat believable but still noticeable.",
        3: "Make the scam convincing with subtle warning signs.",
        4: "Make the scam highly convincing with very subtle red flags."
    }.get(difficulty, "Make the scam realistic.")

    scenario_guidance = {
        "bank_fraud": "A caller pretends to be from a bank fraud department and tries to get account details or one-time codes.",
        "tech_support": "A caller pretends to be tech support and tries to get remote access or frighten the user into acting.",
        "grandparent": "A caller pretends to be a family member in urgent trouble and pressures the user to send money.",
        "government": "A caller pretends to be a government agency and uses threats or legal pressure to demand payment or personal information."
    }.get(scenario_type, "A suspicious scam phone call.")

    prompt_purposes = {
        "opening": "Generate the opening line of the scam call.",
        "ask_for_code": "Generate a follow-up line asking for sensitive verification information or a one-time code.",
        "push_for_account_number": "Generate a line pushing the victim to provide account details.",
        "urgency_if_call_later": "Generate a line using urgency when the victim says to call later.",
        "freeze_account_pressure": "Generate a line threatening account freezing or similar pressure.",
        "fake_name_and_department": "Generate a line where the scammer gives a fake professional identity to sound trustworthy.",
        "remote_access_request": "Generate a line asking the victim to download software or allow remote access.",
        "fake_system_alert": "Generate a line claiming the caller received a technical alert from the victim's device.",
        "family_emergency_opening": "Generate an opening line for a fake family emergency scam.",
        "family_pressure": "Generate a line pressuring the victim not to verify with others and to send money quickly.",
        "government_threat_opening": "Generate an opening line for a government impersonation scam.",
        "gift_card_payment": "Generate a line demanding immediate payment using gift cards or wire transfer.",
        "refuse_documentation": "Generate a line refusing to send official paperwork and pushing urgency."
    }

    purpose_text = prompt_purposes.get(prompt_key, "Generate a realistic scammer line.")

    output_language = get_llm_output_language()

    prompt = f"""
You are generating one short line of spoken dialogue for a cybersecurity training role-play.

Scenario type: {scenario_type}
Scenario guidance: {scenario_guidance}
Dialogue purpose: {purpose_text}
Difficulty level: {difficulty}
Difficulty guidance: {difficulty_text}

Rules:
- Output only the scammer's spoken dialogue.
- Keep it to 1 to 3 sentences.
- Make it realistic, clear, and suitable for older adults in a training setting.
- Write the dialogue in {output_language}.
- No markdown.
- No labels.
- No quotation marks around the whole answer.
- Do not include explicit violence or extreme threats.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )

    result = resp.json()
    print("roleplay raw response:", result)

    if "choices" not in result:
        return jsonify({"success": False, "error": "Groq returned no content"}), 500

    line = result["choices"][0]["message"]["content"].strip()

    if line.startswith("```"):
        line = line.replace("```", "").strip()

    return jsonify({"success": True, "line": line})


################################
#   Phone Roleplay Assessment
################################
@app.route("/phone-roleplay/start-session", methods=["POST"])
def start_phone_roleplay_session():
    data = request.get_json() or {}

    username = session.get("username")
    if not username:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    scenario_type = data.get("scenario_type")
    difficulty_level = int(data.get("difficulty_level", 1))

    if not scenario_type:
        return jsonify({"success": False, "error": "Missing scenario_type"}), 400

    started_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect("silvershieldDatabase.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO phone_roleplay_sessions
            (username, scenario_type, difficulty_level, started_at)
            VALUES (?, ?, ?, ?)
        """, (username, scenario_type, difficulty_level, started_at))
        conn.commit()
        session_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO phone_roleplay_results (session_id)
            VALUES (?)
        """, (session_id,))
        conn.commit()

    return jsonify({"success": True, "session_id": session_id})


@app.route("/phone-roleplay/log-event", methods=["POST"])
def log_phone_roleplay_event():
    data = request.get_json() or {}

    session_id = data.get("session_id")
    event_type = data.get("event_type")
    event_value = data.get("event_value", "")
    time_offset_seconds = data.get("time_offset_seconds", 0)

    if not session_id or not event_type:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    timestamp = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect("silvershieldDatabase.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO phone_roleplay_events
            (session_id, event_type, event_value, timestamp, time_offset_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, event_type, event_value, timestamp, time_offset_seconds))
        conn.commit()

    return jsonify({"success": True})


@app.route("/phone-roleplay/finish-session", methods=["POST"])
def finish_phone_roleplay_session():
    data = request.get_json() or {}

    session_id = data.get("session_id")
    final_outcome = data.get("final_outcome", "")
    score = int(data.get("score", 0))
    attempt_count = int(data.get("attempt_count", 0))
    critical_indicators_found = int(data.get("critical_indicators_found", 0))
    critical_indicators_total = int(data.get("critical_indicators_total", 0))
    used_hint = int(data.get("used_hint", 0))
    behavior_pattern = data.get("behavior_pattern", "")
    feedback_shown = data.get("feedback_shown", "")

    if not session_id:
        return jsonify({"success": False, "error": "Missing session_id"}), 400

    ended_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect("silvershieldDatabase.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT started_at FROM phone_roleplay_sessions
            WHERE id = ?
        """, (session_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "error": "Session not found"}), 404

        started_at = datetime.fromisoformat(row[0])
        ended_dt = datetime.fromisoformat(ended_at)
        total_time_seconds = (ended_dt - started_at).total_seconds()

        cursor.execute("""
            UPDATE phone_roleplay_sessions
            SET ended_at = ?, total_time_seconds = ?, final_outcome = ?, score = ?, completed = 1
            WHERE id = ?
        """, (ended_at, total_time_seconds, final_outcome, score, session_id))

        cursor.execute("""
            UPDATE phone_roleplay_results
            SET attempt_count = ?,
                critical_indicators_found = ?,
                critical_indicators_total = ?,
                used_hint = ?,
                behavior_pattern = ?,
                feedback_shown = ?
            WHERE session_id = ?
        """, (
            attempt_count,
            critical_indicators_found,
            critical_indicators_total,
            used_hint,
            behavior_pattern,
            feedback_shown,
            session_id
        ))

        conn.commit()

    return jsonify({
        "success": True,
        "total_time_seconds": total_time_seconds
    })


@app.route("/phone-roleplay/progress-summary", methods=["GET"])
def phone_roleplay_progress_summary():
    username = session.get("username")
    if not username:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    with sqlite3.connect("silvershieldDatabase.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*), COALESCE(AVG(score), 0), COALESCE(AVG(total_time_seconds), 0)
            FROM phone_roleplay_sessions
            WHERE username = ? AND completed = 1
        """, (username,))
        overall = cursor.fetchone()

        cursor.execute("""
            SELECT scenario_type, COUNT(*), COALESCE(AVG(score), 0)
            FROM phone_roleplay_sessions
            WHERE username = ? AND completed = 1
            GROUP BY scenario_type
        """, (username,))
        by_scenario = cursor.fetchall()

    return jsonify({
        "success": True,
        "overall": {
            "completed_sessions": overall[0],
            "average_score": round(overall[1], 2),
            "average_time_seconds": round(overall[2], 2)
        },
        "by_scenario": [
            {
                "scenario_type": row[0],
                "completed_sessions": row[1],
                "average_score": round(row[2], 2)
            }
            for row in by_scenario
        ]
    })
################################
#         Email AI
################################
@app.route("/generate-email", methods=["POST"])
def generate_email():
    import random as _random
    data = request.get_json(silent=True) or {}
    platform = (data.get("platform") or "desktop").lower()
    category = "difficulty_email_mobile" if platform == "mobile" else "difficulty_email_desktop"
    difficulty = get_difficulty(category)
    output_language = get_llm_output_language()

    is_scam = _random.random() < 0.5
    expected_label = "scam" if is_scam else "not_scam"

    html_structure = """REQUIRED STRUCTURE (must appear exactly like this):
<b>From:</b> sender name &lt;sender@domain.com&gt;<br>
<b>To:</b> user@example.com<br>
<b>Subject:</b> (Generate a natural, realistic subject)<br><br>
<hr><br>

Then generate 2-4 paragraphs using:
<p style="font-family:Arial; font-size:15px; line-height:1.55;"> ... </p>"""

    output_rules = """OUTPUT RULES:
- Output ONLY HTML (no markdown, no comments).
- DO NOT wrap in <html> or <body>.
- DO NOT output code fences (```).
- DO NOT explain anything.
- All text color MUST be black.
- Do NOT use light gray, white, or low-contrast colors.
- Use readable HTML formatting only."""

    if is_scam:
        prompt = f"""You are generating a PHISHING email for a cybersecurity training simulation.

The email must be formatted like a real email using clean HTML:

{html_structure}

{output_rules}

PHISHING RULES:
- Include ONE subtle malicious link.
- Domain should look almost real (e.g. https://login.microsoft-review.com).
- Tone should sound normal, professional, believable.
- Red flags must be subtle at higher difficulty (3-4).
- Write all visible email text in {output_language}.

DIFFICULTY LEVEL: {difficulty}
Generate a NEW realistic PHISHING email now. Do NOT write a real/safe email.
"""
    else:
        prompt = f"""You are generating a LEGITIMATE (real, non-phishing) email for a cybersecurity training simulation.

The email must be formatted like a real email using clean HTML:

{html_structure}

{output_rules}

LEGITIMATE EMAIL RULES:
- No malicious links.
- Natural business or personal tone.
- No unusual urgency or threats.
- No login verification requests.
- Use a real-looking company domain.
- Write all visible email text in {output_language}.

DIFFICULTY LEVEL: {difficulty}
Generate a NEW realistic LEGITIMATE email now. Do NOT write a phishing or scam email.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }

    email_html = None
    for _attempt in range(2):
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        groq_data = resp.json()
        if "choices" not in groq_data:
            continue
        candidate = groq_data["choices"][0]["message"]["content"].strip()
        if candidate.startswith("```"):
            candidate = candidate.replace("```html", "").replace("```", "").strip()
        if len(candidate) >= 10:
            email_html = candidate
            break

    if not email_html:
        return jsonify({"success": False, "error": "Failed to generate email after retries"}), 500

    return jsonify({"success": True, "email": email_html, "expected_label": expected_label})

@app.route("/api/analyze", methods=["POST"])
def analyze_email():
    data = request.get_json() or {}
    output_language = get_llm_output_language()

    # Backward-compatible fallback: mobile clients may still post to /api/analyze.
    if data.get("type"):
        return analyze_any()

    user_choice = data.get("user_choice")
    message = data.get("message")
    expected_label = (data.get("expected_label") or "").strip().lower()
    # Normalize: "fake" -> "scam", "real" -> "not_scam"
    if expected_label == "fake":
        expected_label = "scam"
    elif expected_label == "real":
        expected_label = "not_scam"
    if expected_label not in ("scam", "not_scam"):
        expected_label = ""

    if not user_choice or not message:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    # Normalize user_choice to scam/not_scam for comparison
    normalized_choice = user_choice.strip().lower()
    if normalized_choice == "fake":
        normalized_choice = "scam"
    elif normalized_choice == "real":
        normalized_choice = "not_scam"

    difficulty = get_difficulty("difficulty_email_desktop")

    if expected_label:
        # Deterministic correctness — AI explains why
        is_correct = (normalized_choice == expected_label)
        correct_answer_label = "PHISHING" if expected_label == "scam" else "LEGITIMATE"
        user_answer_label = "FAKE (phishing)" if normalized_choice == "scam" else "REAL (legitimate)"
        explain_prompt = f"""You are a cybersecurity trainer giving feedback on an email classification exercise.

The trainee was shown this email:
--- EMAIL START ---
{message}
--- EMAIL END ---

The correct classification is: {correct_answer_label}
The trainee answered: {user_answer_label} — which is {'CORRECT' if is_correct else 'INCORRECT'}.

Write a 1-2 sentence explanation of WHY this email is {correct_answer_label}, pointing to specific clues in the content.
Then list 2-3 short clue strings.
Write feedback and clues in {output_language}.

Respond ONLY with valid JSON, no markdown:
{{"correct": {'true' if is_correct else 'false'}, "feedback": "explanation here", "clues": ["clue 1", "clue 2"]}}"""
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": explain_prompt}]}
        try:
            groq_resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            raw = groq_resp.json()["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            parsed["correct"] = is_correct  # always enforce deterministic result
        except Exception:
            parsed = {"correct": is_correct, "feedback": f"This email is {correct_answer_label.lower()}.", "clues": []}
    else:
        prompt = f"""
You are analyzing whether an email is REAL (legitimate) or FAKE (phishing).

Here is the email:

--- EMAIL START ---
{message}
--- EMAIL END ---

The user selected: {user_choice.upper()}
Write feedback and clues in {output_language}.

You MUST respond with ONLY a JSON object. Use double quotes. No markdown.
{{"correct": true or false, "feedback": "One sentence.", "clues": ["clue1"]}}
"""

        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
        }
        groq_resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload
        )
        groq_data = groq_resp.json()
        if "choices" not in groq_data:
            return jsonify({"success": False, "error": "Groq API error"}), 500
        raw = groq_data["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"correct": False, "feedback": "Could not parse AI response.", "clues": []}

    # Apply difficulty update
    is_correct = parsed.get("correct", False)
    if is_correct:
        set_difficulty("difficulty_email_desktop", difficulty + 1)
    else:
        set_difficulty("difficulty_email_desktop", 1)

    username = session.get('username')
    if username:
        correct_answer = user_choice if is_correct else ("fake" if user_choice == "real" else "real")
        time_spent = request.get_json().get("time_spent_seconds")
        indicators_found = parsed.get("clues", []) if is_correct else []
        log_scenario_attempt(
            username,
            "email",
            "desktop",
            user_choice,
            correct_answer,
            is_correct,
            difficulty,
            json.dumps(parsed),
            duration_seconds=time_spent,
            message=message,
            indicators_found=indicators_found
        )
        update_module_progress(username, "email_desktop")

    return jsonify({
        "success": True,
        "feedback": parsed,
        "difficulty_now": get_difficulty("difficulty_email_desktop")
    })

################################
#
# Desktop Internet AI
#
#################################
@app.route("/api/generate_sites", methods=["POST"])
def generate_sites():
    import random

    data = request.json
    mode = data.get("mode")
    difficulty = get_difficulty("difficulty_internet_desktop")
    output_language = get_llm_output_language()

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    # Helper: safe JSON extraction
    def safe_extract_json(raw_text):
        raw_text = raw_text.strip()

        # Remove markdown fences if model used them
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(raw_text)
        except:
            return None

    ################################
    # MODE A — Generate LIST OF 5 RESULTS
    ################################
    if mode == "list":

        legit_prompt = f"""
Generate one SAFE, legitimate website search result.

    Write title and description in {output_language}.

Return ONLY JSON:
{
  "title": "Example Title",
  "url": "https://example.com",
  "description": "Short 1-2 sentence description.",
  "site_type": "legit"
}
"""

        phishing_prompt = f"""
Generate one PHISHING website search result.

Rules:
- URL must look similar to a real brand but be wrong
- Subtle phishing tone
- No obvious fake giveaways
    - Write title and description in {output_language}.

Return ONLY JSON:
{
  "title": "Example Scam Title",
  "url": "https://brand-secure-check.com",
  "description": "Short 1-2 sentence phishing lure.",
  "site_type": "phishing"
}
"""

        results = []

        # ---- Generate sites with retry ----
        def generate_one(prompt_text):
            for attempt in range(2):  # try twice
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt_text}]
                }

                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers, json=payload
                )

                try:
                    raw_response = r.json()["choices"][0]["message"]["content"]
                except:
                    continue

                parsed = safe_extract_json(raw_response)
                if parsed:
                    return parsed

            # Fail-safe
            return {
                "title": "Error Loading",
                "url": "about:blank",
                "description": "The AI failed to generate a response.",
                "site_type": "legit"
            }

        # Generate 2 legit sites
        for _ in range(2):
            results.append(generate_one(legit_prompt))

        # Generate 3 phishing sites
        for _ in range(3):
            results.append(generate_one(phishing_prompt))

        random.shuffle(results)

        return jsonify({"success": True, "results": results})

    ################################
    # MODE B — Generate FULL WEBSITE HTML
    ################################
    if mode == "open":
        title = data["title"]
        url = data["url"]
        site_type = data["site_type"]
        difficulty = get_difficulty("difficulty_internet_desktop")

        behavior_text = "This is a SAFE legitimate website." \
            if site_type == "legit" \
            else "This is a PHISHING website designed to trick the user."

        open_prompt = f"""
        You are generating a realistic website.

        DIFFICULTY LEVEL: {difficulty}

        ---
        Difficulty rules:
        1 = Extremely obvious phishing. Wrong logos, bad spelling, weird layout.
        2 = Somewhat suspicious. Slightly weird domain, formatting mistakes.
        3 = Subtle phishing. Looks almost real; small red flags.
        4 = Nearly perfect imitation. Very subtle clues only an expert notices.
        ---

        USER EXPECTATION:
        - Must output ONLY <div>...</div>
        - All text must be black.
        - No <html>, <body>, <script>, markdown, or comments.
        - Write all visible website text in {output_language}.

        SITE TYPE:
        - legit = a completely normal business website
        - phishing = follow difficulty rules above

        TITLE: {title}
        URL: {url}
        NOTES: {"This is a SAFE legitimate website." if site_type == "legit" else "This is a PHISHING website designed to trick the user."}

        Return ONLY HTML. 
        """

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": open_prompt}]
        }

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload
        )

        html = r.json()["choices"][0]["message"]["content"].strip()

        if html.startswith("```"):
            html = html.replace("```html", "").replace("```", "").strip()

    return jsonify({
        "success": True,
        "html": html,
        "site_type": site_type,
        "ai_context": html,
        "difficulty": difficulty
    })

    return jsonify({"success": False, "error": "Invalid mode"}), 400


@app.route("/api/analyze_website", methods=["POST"])
def analyze_website():
    data = request.get_json()
    output_language = get_llm_output_language()

    user_choice = data.get("user_choice")
    html = data.get("ai_context")
    site_type = data.get("site_type")

    if not user_choice or not html or not site_type:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    difficulty = get_difficulty("difficulty_internet_desktop")

    # Deterministic scoring: site_type is ground truth set at generation time.
    # "legit" -> user must pick "real"; "phishing" -> user must pick "fake".
    choice = user_choice.strip().lower()
    if site_type == "phishing":
        is_correct = choice in ("fake", "scam")
        correct_answer_label = "PHISHING"
    else:
        is_correct = choice in ("real", "legit", "not_scam")
        correct_answer_label = "LEGITIMATE"
    user_answer_label = "FAKE (phishing)" if choice in ("fake", "scam") else "REAL (legitimate)"

    explain_prompt = f"""You are a cybersecurity trainer giving feedback on a website classification exercise.

The trainee was shown this website HTML:
--- SITE START ---
{html[:2000]}
--- SITE END ---

The correct classification is: {correct_answer_label}
The trainee answered: {user_answer_label} — which is {'CORRECT' if is_correct else 'INCORRECT'}.

Write a 1-2 sentence explanation of WHY this site is {correct_answer_label}, pointing to specific clues in the content.
Then list 2-3 short clue strings.
Write explanation and clues in {output_language}.

Respond ONLY with valid JSON, no markdown:
{{"correct": {'true' if is_correct else 'false'}, "explanation": "explanation here", "clues": ["clue 1", "clue 2"]}}"""
    headers_ai = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload_ai = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": explain_prompt}]}
    try:
        resp_ai = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers_ai, json=payload_ai)
        raw_ai = resp_ai.json()["choices"][0]["message"]["content"].strip()
        if raw_ai.startswith("```"):
            raw_ai = raw_ai.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw_ai)
        parsed["correct"] = is_correct  # always enforce deterministic result
    except Exception:
        parsed = {"correct": is_correct, "explanation": f"This site is {correct_answer_label.lower()}.", "clues": []}
    if is_correct:
        set_difficulty("difficulty_internet_desktop", difficulty + 1)
    else:
        set_difficulty("difficulty_internet_desktop", 1)

    username = session.get('username')
    if username:
        time_spent = request.get_json().get("time_spent_seconds")
        ai_context = request.get_json().get("ai_context")
        indicators_found = parsed.get("clues", []) if is_correct else []
        log_scenario_attempt(
            username,
            "internet",
            "desktop",
            user_choice,
            site_type,
            is_correct,
            difficulty,
            json.dumps(parsed),
            duration_seconds=time_spent,
            message=ai_context,
            indicators_found=indicators_found
        )
        update_module_progress(username, "internet_desktop")

    return jsonify({
        "success": True,
        "feedback": parsed,
        "difficulty_now": get_difficulty("difficulty_internet_desktop")
    })

################################
#         Mobile SMS
################################
@app.route("/generate-sms", methods=["POST"])
def generate_sms():
    """
    Generates an SMS scam or safe message (randomly chosen).
    Returns JSON.
    """
    import random as _random
    difficulty = get_difficulty("difficulty_sms_mobile")
    output_language = get_llm_output_language()
    is_scam = _random.random() < 0.5
    expected_label = "scam" if is_scam else "not_scam"

    scam_difficulty_text = {
        1: "Make the scam VERY obvious: bad grammar, weird link, over-the-top urgency.",
        2: "Scam is noticeable but not too obvious. Some strange phrasing or link.",
        3: "Mostly convincing SMS with subtle red flags only.",
        4: "Extremely convincing SMS; only trained users notice the clues.",
    }[difficulty]

    safe_difficulty_text = {
        1: "A clearly normal message — no urgency, proper grammar, recognizable brand.",
        2: "A mostly normal message but with a generic tone that could be suspicious.",
        3: "A realistic legitimate notification that looks almost identical to real brand messages.",
        4: "A perfectly legitimate message indistinguishable from real bank/brand texts.",
    }[difficulty]

    theme = request.json.get("theme", "bank / package / delivery / login security")

    if is_scam:
        prompt = f"""
    You generate a REALISTIC PHISHING TEXT MESSAGE. It must look like real scam texts people receive.

    RULES:
    - Output ONLY valid JSON.
    - NO markdown.
    - NO commentary before or after.
    - NO explanations.
    - ONLY the JSON object.
    - Use double quotes.
    - MUST follow this structure exactly:

    {{
      "number": "+1 555 123 4567",
      "text": "SMS message body...",
      "time": "10:52 AM",
      "clues": ["scam clue 1", "scam clue 2"]
    }}

    REALISM REQUIREMENTS:
    - Must imitate real scam SMS patterns.
    - Use typo-squatted brands (Amzon, PayPall, US Postal Servce).
    - Include urgency, threats, refunds, delivery issues, bank locks.
    - Include a suspicious, shortened, or weird URL.
    - NEVER mention SilverShield.
    - Write the SMS text and clues in {output_language}.

    TASK:
    Create **one** SCAM SMS message.
    Difficulty = {difficulty}
    Style = {scam_difficulty_text}
    Theme = {theme}

    FINAL RULE:
    Respond with ONLY the JSON object. NOTHING else.
    """
    else:
        prompt = f"""
    You generate a REALISTIC LEGITIMATE TEXT MESSAGE from a real company or service.

    RULES:
    - Output ONLY valid JSON.
    - NO markdown.
    - NO commentary before or after.
    - NO explanations.
    - ONLY the JSON object.
    - Use double quotes.
    - MUST follow this structure exactly:

    {{
      "number": "+1 555 123 4567",
      "text": "SMS message body...",
      "time": "10:52 AM",
      "clues": []
    }}

    REALISM REQUIREMENTS:
    - Must look like a real notification from a well-known brand (Amazon, Chase Bank, UPS, etc.).
    - Use correct brand names and professional tone.
    - Include a legitimate-looking URL from the real brand domain.
    - NO urgency or threats. Just a routine update, delivery notification, or account alert.
    - NEVER mention SilverShield.
    - Write the SMS text in {output_language}.

    TASK:
    Create **one** LEGITIMATE SMS message.
    Difficulty = {difficulty}
    Style = {safe_difficulty_text}
    Theme = {theme}

    FINAL RULE:
    Respond with ONLY the JSON object. NOTHING else.
    """

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=payload)

    data = r.json()

    if "choices" not in data:
        return jsonify({"success": False, "error": "Groq returned no choices"}), 500

    raw = data["choices"][0]["message"]["content"].strip()

    # Handle markdown
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    # Cut trailing noise
    last = raw.rfind("}")
    if last != -1:
        raw = raw[:last+1]

    try:
        sms_obj = json.loads(raw)
    except Exception:
        return jsonify({
            "success": True,
            "difficulty": difficulty,
            "sms": {
                "number": "+1 000 000 0000",
                "text": "Failed to generate message. Try again.",
                "time": "12:00 PM",
                "clues": []
            }
        })

    return jsonify({
        "success": True,
        "difficulty": difficulty,
        "expected_label": expected_label,
        "sms": sms_obj
    })


################################
#       Mobile Call
################################
@app.route("/generate-call", methods=["POST"])
def generate_call():
    import random as _random
    difficulty = get_difficulty("difficulty_call_mobile")
    output_language = get_llm_output_language()
    is_scam = _random.random() < 0.5
    expected_label = "scam" if is_scam else "not_scam"

    scam_difficulty_text = {
        1: "Obvious scam: caller is clearly suspicious.",
        2: "Moderately subtle scam: some clues remain.",
        3: "Convincing scam: only subtle clues.",
        4: "Extremely convincing scam: only experts notice the red flags.",
    }[difficulty]

    safe_difficulty_text = {
        1: "Clearly legitimate: professional tone, no pressure, easy to identify as real.",
        2: "Legitimate but with a generic script that could raise mild doubt.",
        3: "Realistic legitimate call with subtle details that confirm it's real.",
        4: "Perfect legitimate call — indistinguishable from a real company rep.",
    }[difficulty]

    theme = request.json.get("theme", "government agency or tech support")

    if is_scam:
        prompt = f"""
You are generating a REALISTIC PHONE SCAM CALL TRANSCRIPT.

STRICT RULES:
- Output ONLY VALID JSON.
- No markdown.
- No text outside the JSON.
- JSON MUST follow:

{{
  "number": "(555) 123-9876",
  "caller_name": "string",
  "transcript": "Full transcript with \\n line breaks.",
  "clues": ["clue1", "clue2"]
}}

TASK:
Difficulty={difficulty}
{scam_difficulty_text}
Theme={theme}
Write caller_name, transcript, and clues in {output_language}.
"""
    else:
        prompt = f"""
You are generating a REALISTIC LEGITIMATE PHONE CALL TRANSCRIPT from a real company or service.

STRICT RULES:
- Output ONLY VALID JSON.
- No markdown.
- No text outside the JSON.
- JSON MUST follow:

{{
  "number": "(800) 123-4567",
  "caller_name": "string",
  "transcript": "Full transcript with \\n line breaks.",
  "clues": []
}}

REQUIREMENTS:
- Caller represents a real well-known company (e.g. Chase Bank, UPS, Amazon).
- Professional tone. No threats, no urgency, no requests for passwords or gift cards.
- Routine purpose: appointment reminder, delivery update, account notification.
- NEVER mention SilverShield.

TASK:
Difficulty={difficulty}
{safe_difficulty_text}
Theme={theme}
Write caller_name and transcript in {output_language}.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=payload)
    data = r.json()

    if "choices" not in data:
        return jsonify({"success": False, "error": "Groq error"}), 500

    raw = data["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    last = raw.rfind("}")
    raw = raw[:last+1]

    try:
        call_obj = json.loads(raw)
    except Exception:
        return jsonify({"success": False, "error": "Invalid JSON"}), 500

    return jsonify({
        "success": True,
        "difficulty": difficulty,
        "expected_label": expected_label,
        "call": call_obj
    })


################################
#        Mobile Web
################################
@app.route("/generate-web", methods=["POST"])
def generate_web():
    import random as _random
    difficulty = get_difficulty("difficulty_web_mobile")
    output_language = get_llm_output_language()
    is_scam = _random.random() < 0.5
    expected_label = "scam" if is_scam else "not_scam"

    scam_difficulty_text = {
        1: "Obvious scam: typo-squatted URLs, suspicious ads.",
        2: "Somewhat suspicious: some red-flag links.",
        3: "Subtle clues only: nearly convincing fake results.",
        4: "Nearly perfect scam site — only an expert would notice.",
    }[difficulty]

    safe_difficulty_text = {
        1: "Clearly legitimate results: real brand domains, no suspicious ads.",
        2: "Mostly legitimate with generically-worded ads that could raise mild doubt.",
        3: "Realistic legitimate search page — very close to real Google results.",
        4: "Perfect search results page indistinguishable from real Google.",
    }[difficulty]

    theme = request.json.get("theme", "search / login / refund / alert")

    if is_scam:
        prompt = f"""
Generate extremely realistic FAKE GOOGLE SEARCH RESULTS that contain scam content.

STRICT RULES:
- Output ONLY JSON.
- NO markdown.
- Follow this structure:

{{
    "ads": [{{"title":"...", "url":"...", "snippet":"..."}}],
    "results": [{{"title":"...", "url":"...", "snippet":"..."}}],
  "pagination": {{
      "next_page_label": "Next >",
      "page_number": 1
  }},
  "clues": ["...", "..."]
}}

- Return exactly 2 ads and exactly 6 results.
- Every ad/result item must include non-empty "title", "url", and "snippet" strings.

Difficulty={difficulty}
{scam_difficulty_text}
Theme={theme}
Write all ad/result text and clues in {output_language}.
"""
    else:
        prompt = f"""
Generate extremely realistic LEGITIMATE GOOGLE SEARCH RESULTS from real companies and brands.

STRICT RULES:
- Output ONLY JSON.
- NO markdown.
- Follow this structure:

{{
    "ads": [{{"title":"...", "url":"...", "snippet":"..."}}],
    "results": [{{"title":"...", "url":"...", "snippet":"..."}}],
  "pagination": {{
      "next_page_label": "Next >",
      "page_number": 1
  }},
  "clues": []
}}

- Return exactly 2 ads and exactly 6 results.
- Every ad/result item must include non-empty "title", "url", and "snippet" strings.

REQUIREMENTS:
- Use real well-known brand domains (amazon.com, chase.com, usps.com, etc.).
- Professional ad copy and descriptions.
- No typo-squatted URLs, no suspicious links.
- NEVER mention SilverShield.

Difficulty={difficulty}
{safe_difficulty_text}
Theme={theme}
Write all ad/result text in {output_language}.
"""

    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=payload)

    raw = r.json()["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        web_obj = json.loads(raw)
    except:
        return jsonify({"success": False, "error": "Invalid JSON"}), 500

    # Normalize LLM output so the frontend always gets consistent fields.
    def normalize_item(item):
        if not isinstance(item, dict):
            return None

        title = (item.get("title") or item.get("headline") or item.get("name") or "").strip()
        url = (item.get("url") or item.get("link") or item.get("domain") or "").strip()
        snippet = (item.get("snippet") or item.get("description") or item.get("text") or "").strip()

        if not title and not url and not snippet:
            return None

        return {
            "title": title,
            "url": url,
            "snippet": snippet,
        }

    ads = [normalize_item(x) for x in (web_obj.get("ads") or [])]
    results = [normalize_item(x) for x in (web_obj.get("results") or [])]

    web_obj["ads"] = [x for x in ads if x][:2]
    web_obj["results"] = [x for x in results if x][:6]

    return jsonify({
        "success": True,
        "difficulty": difficulty,
        "expected_label": expected_label,
        "web": web_obj
    })

@app.route("/api/analyze_any", methods=["POST"])
def analyze_any():
    """
    Unified analyzer for: desktop email, desktop internet,
    mobile SMS, mobile call, mobile web.

    Expected JSON:
    {
        "type": "email" | "internet" | "sms" | "call" | "web",
        "user_choice": "scam" | "not_scam" | "fake" | "real",
        "message": "<content the user saw>"
    }
    """

    data = request.get_json() or {}
    output_language = get_llm_output_language()
    msg_type = data.get("type", "").lower()
    time_spent = data.get("time_spent_seconds")
    user_choice = data.get("user_choice")
    message = data.get("message")

    if not msg_type or not user_choice or not message:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    #Normalize user choice
    choice = user_choice.strip().lower()
    if choice == "fake":
        choice = "scam"
    elif choice == "real":
        choice = "not_scam"

    #Map type → difficulty column name
    difficulty_map = {
        "email": "difficulty_email_desktop",
        "internet": "difficulty_internet_desktop",
        "sms": "difficulty_sms_mobile",
        "call": "difficulty_call_mobile",
        "web": "difficulty_web_mobile",
    }

    if msg_type not in difficulty_map:
        return jsonify({"success": False, "error": "Unknown message type"}), 400

    platform_map = {
        "email": "desktop",
        "internet": "desktop",
        "sms": "mobile",
        "call": "mobile",
        "web": "mobile",
    }

    platform = platform_map[msg_type]

    # Allow caller to override platform (e.g. mobile email vs desktop email)
    request_platform = data.get("platform", "").lower()
    if request_platform in ("mobile", "desktop"):
        platform = request_platform

    category = difficulty_map[msg_type]
    if msg_type == "email" and platform == "mobile":
        category = "difficulty_email_mobile"

    difficulty = get_difficulty(category)

    #Human-readable label (for prompt)
    type_label = {
        "email": "EMAIL",
        "internet": "WEBPAGE / SEARCH RESULT",
        "sms": "TEXT MESSAGE (SMS)",
        "call": "PHONE CALL TRANSCRIPT",
        "web": "MOBILE WEBPAGE / SEARCH RESULT"
    }.get(msg_type, "MESSAGE")

    expected_label = data.get("expected_label")
    if isinstance(expected_label, str):
        expected_label = expected_label.strip().lower()
        if expected_label == "fake":
            expected_label = "scam"
        elif expected_label == "real":
            expected_label = "not_scam"
        if expected_label not in ("scam", "not_scam"):
            expected_label = None
    else:
        expected_label = None

    if expected_label:
        is_correct_local = (choice == expected_label)
        correct_answer_label = "SCAM" if expected_label == "scam" else "LEGITIMATE"
        user_answer_label = "SCAM" if choice == "scam" else "LEGITIMATE"
        explain_prompt = f"""You are a cybersecurity trainer giving feedback on a {type_label} classification exercise.

The trainee was shown this content:
--- CONTENT START ---
{message[:2000]}
--- CONTENT END ---

The correct classification is: {correct_answer_label}
The trainee answered: {user_answer_label} — which is {'CORRECT' if is_correct_local else 'INCORRECT'}.

Write a 1-2 sentence explanation of WHY this content is {correct_answer_label}, pointing to specific clues.
Then list 2-3 short clue strings.
Write feedback and clues in {output_language}.

Respond ONLY with valid JSON, no markdown:
{{"correct": {'true' if is_correct_local else 'false'}, "feedback": "explanation here", "clues": ["clue 1", "clue 2"]}}"""
        headers_ex = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        payload_ex = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": explain_prompt}]}
        try:
            r_ex = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers_ex, json=payload_ex)
            raw_ex = r_ex.json()["choices"][0]["message"]["content"].strip()
            if raw_ex.startswith("```"):
                raw_ex = raw_ex.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw_ex)
            parsed["correct"] = is_correct_local  # enforce deterministic result
        except Exception:
            parsed = {"correct": is_correct_local, "feedback": f"This {type_label.lower()} is {correct_answer_label.lower()}.", "clues": []}
    else:
        # -------------------------------------------
        # Build AI prompt
        # -------------------------------------------
        prompt = f"""
You are a cybersecurity training AI.

The trainee reviewed the following {type_label}:

--- USER CONTENT START ---
{message}
--- USER CONTENT END ---

The trainee selected: {choice.upper()} (SCAM vs NOT SCAM)

### STRICT RULES ###
- Respond ONLY with valid JSON.
- No markdown.
- No commentary outside the JSON.
- Use DOUBLE QUOTES.
- Write feedback and clues in {output_language}.

### REQUIRED JSON OUTPUT ###
{{
  "correct": true or false,
  "feedback": "One or two sentence explanation.",
  "clues": ["short clue 1", "short clue 2"]
}}
"""

        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
        }

        #Call Groq API
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers=headers, json=payload)

        data = r.json()
        print("UNIFIED ANALYZER RAW:", data)

        if "choices" not in data:
            return jsonify({"success": False, "error": "Groq returned no choices"}), 500

        raw = data["choices"][0]["message"]["content"].strip()

        #Clean JSON fences
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        #Parse JSON safely
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "correct": False,
                "feedback": "AI response could not be parsed.",
                "clues": []
            }

    #####################
    # Updating difficulty
    #####################
    is_correct = parsed.get("correct", False)
    if is_correct:
        set_difficulty(category, difficulty + 1)
    else:
        set_difficulty(category, 1)

    username = session.get('username')
    if username:
        correct_answer = choice if is_correct else ("not_scam" if choice == "scam" else "scam")
        scenario_type_full = f"{msg_type}_{platform}"
        indicators_found = parsed.get("clues", []) if is_correct else []
        log_scenario_attempt(
            username,
            scenario_type_full,
            platform,
            choice,
            correct_answer,
            is_correct,
            difficulty,
            json.dumps(parsed),
            duration_seconds=time_spent,
            message=message,
            indicators_found=indicators_found
        )
        update_module_progress(username, scenario_type_full)

    return jsonify({
        "success": True,
        "feedback": parsed,
        "difficulty_now": get_difficulty(category)
    })

#Main
if __name__ == '__main__':
    app.run(debug=True)
