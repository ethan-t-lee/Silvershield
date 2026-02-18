Silvershield - Cybersecurity Training Simulator

Silvershield is an education web app that simulates phishing, scam SMS, scam call, and malicious site scenarios to help older users learn to spot cyber threats. The platform provides fake but realistic phishing emails, scam calls, scam text messages, and fake websites, and lets users guess whether something is a scam or safe. The system will provide feedback and adjust the difficulty of each simulation as needed.

⭐ Features
- Generate realistic phishing or legitimate content for:
  - Email (Mobile & Desktop)
  - SMS (Mobile)
  - Phone Calls (Mobile)
  - Web/Search Results (Mobile & Desktop)
- Interactive UI simulating a mobil phone for SMS/Call/Web scenarios
- Session-based user login/registration and two factor authentication
- Difficulty tracking per user and per content type
- Feedback system as user marks a scenario as "real" or "fake"
- SQLite database for user data and difficulty settings

⭐ Getting Started - Local setup
Prerequisies:
  - Python 3.8
  - pip for python packages
  - (Optional) Virtual Environment

Installation & Run
1. Clone the repo
git clone https://github.com/ethan-t-lee/Silvershield.git
cd Silvershield

2. Install dependencies
pip install -r requirements.txt   # or manually install Flask, requests, etc.

3. Create a `.env` file for API keys (use the provided `.env.example` as a template)
- The project reads all secrets from a single `.env` file at startup.
- Required variables (in `.env`): `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_VERIFY_SID`, `GROQ_KEY`

4. Run the server
python app.py

NOTE: You will need to create a GROQ and Twilio account to generate the neccessary keys for this project to work.
