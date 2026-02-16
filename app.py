from flask import Flask, render_template, request, jsonify, flash, session
from user_login import user_registration, verifying_login
from TWOFA import send_otp, verify_otp
from config.GROQKEY import GROQ_KEY
import sqlite3
import json
import requests
import database
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

app.secret_key = "SECRET KEY"

################################
# Loading difficulty from
#       the database
################################
def get_difficulty(category):
    username = session.get('username')
    if not username:
        return 1

    with sqlite3.connect('silvershieldDatabase.db') as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT {category} FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()

    return row[0] \
        if row \
        else 1

################################
# Saving difficulty to the
#        database
################################
def set_difficulty(category, level):
    #1 - easy, 2 - medium, 3 - hard, 4 - very hard
    level = max(1, min(4, level))

    username = session.get('username')
    if not username:
        return

    with sqlite3.connect('silvershieldDatabase.db') as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE users SET {category} = ? WHERE username = ?', (level, username))
        conn.commit()

################################
#         Page routes
################################
@app.route('/')
def index():
    return render_template("homePage.html")

@app.route('/login', methods=['GET'])
def login():
    return render_template("loginPage.html")

@app.route('/account_creation')
def account_creation():
    return render_template("accountCreation.html")

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/module1')
def module1():
    return render_template("desktopPage.html")


@app.route('/module2')
def module2():
    return render_template("MobilePage.html")

@app.route('/logout')
def logout():
    flash('You have been logged out.', 'info')
    return render_template("loginPage.html")

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
#Login route for credential validation and OTP verification
@app.route('/login', methods=['POST'])
def login_post():
    usernameorEmail = request.form['username'].strip()
    password = request.form['password'].strip()

    valid, phone = verifying_login(usernameorEmail, password)

    if not valid:
        return jsonify({"success": False, "message": "Invalid username or password"})

    if not phone.startswith("+"):
        phone = "+1" + phone

    #Storing logged in user for session
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

################################
#         Email AI
################################
@app.route("/generate-email", methods=["POST"])
def generate_email():
    difficulty = get_difficulty("difficulty_email_desktop")

    # Main generation prompt
    prompt = f"""
You are generating an email for a cybersecurity training simulation.

The email must be formatted like a real email using clean HTML:

REQUIRED STRUCTURE (must appear exactly like this):
<b>From:</b> sender name &lt;sender@domain.com&gt;<br>
<b>To:</b> user@example.com<br>
<b>Subject:</b> (Generate a natural, realistic subject)<br><br>
<hr><br>

Then generate 2–4 paragraphs using:
<p style="font-family:Arial; font-size:15px; line-height:1.55;"> ... </p>

OUTPUT RULES:
- Output ONLY HTML (no markdown, no comments).
- DO NOT wrap in <html> or <body>.
- DO NOT output code fences (```).
- DO NOT explain anything.
- All text color MUST be black.
- Do NOT use light gray, white, or low-contrast colors.
- Use readable HTML formatting only.

=========================================================
EMAIL TYPE RULES
=========================================================

You must generate either a REAL or a FAKE PHISHING email.

A REAL email:
- No malicious links
- Natural business/personal tone
- No unusual urgency or threats
- No login verification requests

A PHISHING email:
- Include ONE subtle malicious link
- Domain should look almost real (ex: https://login.microsoft-review.com)
- Tone should sound normal, professional, believable
- Red flags must be subtle at higher difficulty (3–4)

=========================================================
FEW-SHOT EXAMPLES (for training)
=========================================================

### REAL EMAIL EXAMPLE:
<b>From:</b> Sarah Matthews &lt;smatthews@northwoodanalytics.com&gt;<br>
<b>To:</b> user@example.com<br>
<b>Subject:</b> Quick follow-up before tomorrow’s meeting<br><br>
<hr><br>
<p style="font-family:Arial; font-size:15px; line-height:1.55;">
Just checking in before tomorrow’s review session. Let me know if you'd
like the updated cost breakdown beforehand.
</p>
<p style="font-family:Arial; font-size:15px; line-height:1.55;">
I’ll also bring the revised slide deck in case we need to adjust the rollout plan.
</p>
<p style="font-family:Arial; font-size:15px; line-height:1.55;">
Thanks,<br>Sarah
</p>


### PHISHING EMAIL EXAMPLE:
<b>From:</b> Account Security Team &lt;alerts@secure-auth-center.com&gt;<br>
<b>To:</b> user@example.com<br>
<b>Subject:</b> Action Required: Verify Account Credentials<br><br>
<hr><br>
<p style="font-family:Arial; font-size:15px; line-height:1.55;">
A recent update requires users to confirm account settings. Access may be limited
until verification is completed.
</p>
<p style="font-family:Arial; font-size:15px; line-height:1.55;">
Please verify your details here:<br>
<a href="https://secure-check-auth-review.com/login">
Security Verification Portal
</a>
</p>
<p style="font-family:Arial; font-size:15px; line-height:1.55;">
This process typically takes less than two minutes.
</p>

=========================================================
DIFFICULTY LEVEL: {difficulty}
Generate a NEW realistic email now.
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

    data = resp.json()

    if "choices" not in data:
        return jsonify({"success": False, "error": "Groq returned no content"}), 500

    email_html = data["choices"][0]["message"]["content"].strip()

    # --- Remove accidental markdown fences ---
    if email_html.startswith("```"):
        email_html = email_html.replace("```html", "").replace("```", "").strip()

    # --- Safety fallback ---
    if len(email_html) < 10:
        email_html = "<p style='color:red;'>Error generating email.</p>"

    return jsonify({"success": True, "email": email_html})

@app.route("/api/analyze", methods=["POST"])
def analyze_email():
    data = request.get_json()

    user_choice = data.get("user_choice")
    message = data.get("message")

    if not user_choice or not message:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    difficulty = get_difficulty("difficulty_email_desktop")

    prompt = f"""
You are analyzing whether an email is REAL (legitimate) or FAKE (phishing).

Here is the email:

--- EMAIL START ---
{message}
--- EMAIL END ---

The user selected: {user_choice.upper()}

======================================================
FEW-SHOT TRAINING EXAMPLES
======================================================

### Example: phishing
Email includes harmful link, odd domain, or suspicious request.
Correct output:
{{
  "correct": true,
  "feedback": "This is a phishing email. The domain and request are suspicious.",
  "clues": ["Suspicious link", "Urgency", "Unusual domain"]
}}

### Example: real
Email contains normal communication and no malicious links.
Correct output:
{{
  "correct": true,
  "feedback": "This is a legitimate email with no phishing indicators.",
  "clues": ["No harmful links", "Routine message"]
}}

======================================================
RESPONSE FORMAT RULES
======================================================
You MUST respond with ONLY a JSON object.
Use double quotes.
No markdown.
No code blocks.
No text outside JSON.
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
        headers=headers,
        json=payload
    )

    data = groq_resp.json()

    if "choices" not in data:
        return jsonify({"success": False, "error": "Groq API error"}), 500

    raw = data["choices"][0]["message"]["content"].strip()

    # Strip accidental code fences
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    # Parse JSON
    try:
        parsed = json.loads(raw)
    except Exception:
        return jsonify({
            "success": True,
            "feedback": {
                "correct": False,
                "feedback": "Could not parse AI response.",
                "clues": []
            },
            "difficulty_now": difficulty
        })

    # Apply difficulty update
    if parsed.get("correct") is True:
        set_difficulty("difficulty_email_desktop", difficulty + 1)
    else:
        set_difficulty("difficulty_email_desktop", 1)

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

        legit_prompt = """
Generate one SAFE, legitimate website search result.

Return ONLY JSON:
{
  "title": "Example Title",
  "url": "https://example.com",
  "description": "Short 1-2 sentence description.",
  "site_type": "legit"
}
"""

        phishing_prompt = """
Generate one PHISHING website search result.

Rules:
- URL must look similar to a real brand but be wrong
- Subtle phishing tone
- No obvious fake giveaways

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

    user_choice = data.get("user_choice")
    html = data.get("ai_context")
    site_type = data.get("site_type")

    if not user_choice or not html or not site_type:
        return jsonify({"success": False, "error": "Missing fields"}), 400

    difficulty = get_difficulty("difficulty_internet_desktop")

    prompt = f"""
You are a cybersecurity classifier.

Determine if the website shown below is SAFE (legit) or PHISHING.

==============================
WEBSITE HTML CONTENT:
{html}
==============================

True classification: {site_type}
User selected: {user_choice}

Return ONLY JSON:
{{
  "correct": true/false,
  "explanation": "Short explanation.",
  "clues": ["...", "..."]
}}

NO markdown.
NO commentary.
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
        headers=headers, json=payload
    )

    raw = resp.json()["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except:
        return jsonify({
            "success": True,
            "feedback": {
                "correct": False,
                "explanation": "Could not parse AI response.",
                "clues": []
            }
        })

    # Difficulty adjustment
    if parsed.get("correct"):
        set_difficulty("difficulty_internet_desktop", difficulty + 1)
    else:
        set_difficulty("difficulty_internet_desktop", 1)

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
    Generates an SMS scam or safe message.
    Returns JSON.
    """
    difficulty = get_difficulty("difficulty_sms_mobile")

    difficulty_text = {
        1: "Make the scam VERY obvious: bad grammar, weird link, over-the-top urgency.",
        2: "Scam is noticeable but not too obvious. Some strange phrasing or link.",
        3: "Mostly convincing SMS with subtle red flags only.",
        4: "Extremely convincing SMS; only trained users notice the clues.",
    }[difficulty]

    theme = request.json.get("theme", "bank / package / delivery / login security")

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

    TASK:
    Create **one** SMS message.
    Difficulty = {difficulty}
    Style = {difficulty_text}
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
        "sms": sms_obj
    })


################################
#       Mobile Call
################################
@app.route("/generate-call", methods=["POST"])
def generate_call():
    difficulty = get_difficulty("difficulty_call_mobile")

    difficulty_text = {
        1: "Obvious scam: caller is clearly suspicious.",
        2: "Moderately subtle scam: some clues remain.",
        3: "Convincing scam: only subtle clues.",
        4: "Extremely convincing scam: only experts notice the red flags.",
    }[difficulty]

    theme = request.json.get("theme", "government agency or tech support")

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
{difficulty_text}
Theme={theme}
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
        "call": call_obj
    })


################################
#        Mobile Web
################################
@app.route("/generate-web", methods=["POST"])
def generate_web():
    difficulty = get_difficulty("difficulty_web_mobile")

    difficulty_text = {
        1: "Obvious scam.",
        2: "Somewhat suspicious.",
        3: "Subtle clues only.",
        4: "Nearly perfect scam site.",
    }[difficulty]

    theme = request.json.get("theme", "search / login / refund / alert")

    prompt = f"""
Generate extremely realistic FAKE GOOGLE SEARCH RESULTS.

STRICT RULES:
- Output ONLY JSON.
- NO markdown.
- Follow this structure:

{{
  "ads": [...],
  "results": [...],
  "pagination": {{
      "next_page_label": "Next >",
      "page_number": 1
  }},
  "clues": ["...", "..."]
}}

Difficulty={difficulty}
{difficulty_text}
Theme={theme}
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

    return jsonify({
        "success": True,
        "difficulty": difficulty,
        "web": web_obj
    })

################################
#   Unified Analyzer mostly
#   used for the mobile apps
################################
@app.route("/api/analyze", methods=["POST"])
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
    msg_type = data.get("type", "").lower()
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

    category = difficulty_map[msg_type]
    difficulty = get_difficulty(category)

    #Human-readable label (for prompt)
    type_label = {
        "email": "EMAIL",
        "internet": "WEBPAGE / SEARCH RESULT",
        "sms": "TEXT MESSAGE (SMS)",
        "call": "PHONE CALL TRANSCRIPT",
        "web": "MOBILE WEBPAGE / SEARCH RESULT"
    }.get(msg_type, "MESSAGE")

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
    if parsed.get("correct") is True:
        set_difficulty(category, difficulty + 1)
    else:
        set_difficulty(category, 1)

    return jsonify({
        "success": True,
        "feedback": parsed,
        "difficulty_now": get_difficulty(category)
    })

#Main
if __name__ == '__main__':
    app.run(debug=True)
