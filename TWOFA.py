import os
from twilio.rest import Client


def _get_twilio_client_and_service():
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    verify_sid = os.getenv('TWILIO_VERIFY_SID')

    if not account_sid or not auth_token or not verify_sid:
        raise RuntimeError("Missing Twilio environment variables. Ensure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_VERIFY_SID are set in your .env")

    client = Client(account_sid, auth_token)
    return client, verify_sid


def send_otp(phone):
    client, verify_sid = _get_twilio_client_and_service()
    client.verify.v2.services(verify_sid).verifications.create(to=phone, channel="sms")


def verify_otp(phone, code):
    client, verify_sid = _get_twilio_client_and_service()
    check = client.verify.v2.services(verify_sid).verification_checks.create(to=phone, code=code)
    return check.status == "approved"

