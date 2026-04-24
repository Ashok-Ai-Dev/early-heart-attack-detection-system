import logging
import time
from services.email_service import send_email_alert
from services.sms_service import send_sms_alert

logger = logging.getLogger(__name__)

# Very simple in-memory cooldown structure to prevent spam
# Format: { 'email': last_sent_timestamp }
alert_cooldowns = {}
COOLDOWN_SECONDS = 300  # 5 minutes

def send_alert(user_email: str, risk_score: float, risk_level: str, user_name: str = "User", user_phone: str = None):
    # Check cooldown
    current_time = time.time()
    last_sent = alert_cooldowns.get(user_email, 0)

    if current_time - last_sent < COOLDOWN_SECONDS:
        logger.info(f"Alert for {user_email} skipped due to 5-min cooldown.")
        return False
    
    success = False
    
    # 1. Send Email
    if user_email:
        email_sent = send_email_alert(user_email, user_name, risk_score, risk_level)
        if email_sent:
            success = True

    # 2. Send SMS (if phone provided)
    if user_phone:
        sms_sent = send_sms_alert(user_phone)
        if sms_sent:
            success = True
            
    # If any alert was successful, update the cooldown
    if success:
        alert_cooldowns[user_email] = current_time
        
    return success
