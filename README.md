## Silvershield - Cybersecurity Training Simulator

Silvershield is an education web app that simulates phishing, scam SMS, scam call, and malicious site scenarios to help older users learn to spot cyber threats. The platform provides fake but realistic phishing emails, scam calls, scam text messages, and fake websites, and lets users guess whether something is a scam or safe. The system will provide feedback and adjust the difficulty of each simulation as needed.

Features
- Realistic training scenarios for:
  - Email (Mobile & Desktop)
  - SMS (Mobile)
  - Phone Calls (Mobile)
  - Web/Search Results (Mobile & Desktop)
- New Module 3 phone scam role-play where users practice choosing safe responses during live-style calls
- Read Aloud support in the role-play simulator so users can hear call dialogue during practice
- Interactive UI that simulates mobile and desktop experiences for hands-on learning
- Secure account system with login, registration, and two-factor authentication
- Learning dashboard with progress tracking, attempt history, and performance analytics
- Pre-survey and post-survey flow to measure confidence and learning outcomes over time
- Adaptive difficulty and feedback that respond to each user's choices
- SQLite database for saving user progress, role-play sessions, and training results

Getting Started - Local setup
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

## Deploying to Render

1. Push this repository to GitHub.
2. In Render, create a new **Web Service** and connect the repo.
3. Render will use the included `render.yaml` blueprint automatically.
4. Set the required environment variables in Render:
   - `SECRET_KEY`
   - `GROQ_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_VERIFY_SID`
5. The service will start with:
   ```bash
   gunicorn app:app
   ```

Note: this project currently uses SQLite, so database contents may reset on free hosting after redeploys or restarts.

### Temporary database download route
For short-term debugging, you can set `DB_DOWNLOAD_TOKEN` and visit:

```text
https://your-render-url/admin/download-db?token=your-token-here
```

Remove or unset this token after downloading the file.

## Automated Testing

Run the test suite locally with:

```bash
pytest
```

What is included:
- `pytest`-based automated unit and route tests under `tests/`
- `pytest.ini` for test discovery and configuration
- GitHub Actions workflow at `.github/workflows/python-tests.yml` to run tests on pushes and pull requests

NOTE: You will need to create a GROQ and Twilio account to generate the neccessary keys for this project to work.
