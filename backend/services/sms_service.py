import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_sms_alert(user_phone: str, msg_body: str = None):
    twilio_sid = os.getenv("TWILIO_SID")
    twilio_auth = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone = os.getenv("TWILIO_PHONE")

    if not all([twilio_sid, twilio_auth, twilio_phone]):
        logger.error("Twilio credentials not configured in environment variables.")
        return False

    if not user_phone:
        logger.error("No recipient phone number provided for SMS alert.")
        return False

    if not msg_body:
        msg_body = "High heart attack risk detected. Seek medical attention."

    try:
        client = Client(twilio_sid, twilio_auth)
        message = client.messages.create(
            body=msg_body,
            from_=twilio_phone,
            to=user_phone
        )
        logger.info(f"SMS alert sent successfully. SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS alert: {e}")
        return False
