import os
from twilio.rest import Client

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
verify_sid = os.environ['TWILIO_VERIFY_SID']
client = Client(account_sid, auth_token)

def send_otp(phone):
    client.verify.v2.services(verify_sid).verifications.create(to = phone, channel = "sms")

def verify_otp(phone, code):
    check = client.verify.v2.services(verify_sid).verification_checks.create(to = phone, code = code)
    return check.status == "approved"
