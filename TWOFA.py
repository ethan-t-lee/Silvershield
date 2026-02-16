from twilio.rest import Client

ACCOUNT_SID = "your_account_sid"
AUTH_TOKEN = "your_auth_token"
VERIFY_SID = "your_verification_sid"
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_otp(phone):
    client.verify.v2.services(VERIFY_SID).verifications.create(to = phone, channel = "sms")

def verify_otp(phone, code):
    check = client.verify.v2.services(VERIFY_SID).verification_checks.create(to = phone, code = code)
    return check.status == "approved"