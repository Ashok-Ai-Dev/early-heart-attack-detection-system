import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

def send_email_alert(user_email: str, user_name: str, risk_score: float, risk_level: str):
    sender_email = os.getenv("EMAIL_USER")
    sender_pass = os.getenv("EMAIL_PASS")

    if not sender_email or not sender_pass:
        logger.error("Email credentials not configured in environment variables.")
        return False
        
    # We might not have user_email from the frontend in the predict request, 
    # but the prompt specifies send_alert(user_email, risk_score, risk_level).
    if not user_email:
        logger.error("No recipient email provided.")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user_email
    msg['Subject'] = f"Heart Health Alert: {risk_level} Risk Detected"

    body = (
        f"Dear {user_name},\n\n"
        f"⚠️ High Risk Detected ({risk_score}%).\n\n"
        f"Please consult a doctor immediately.\n\n"
        f"Health suggestions:\n"
        f"- Seek immediate medical attention or call an emergency service if you experience chest pain, shortness of breath, etc.\n"
        f"- Do not ignore these warning signs.\n\n"
        f"Stay safe,\nHeart Health Monitor"
    )

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Assuming Gmail SMTP for this example
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_pass)
        text = msg.as_string()
        server.sendmail(sender_email, user_email, text)
        server.quit()
        logger.info(f"Email alert sent successfully to {user_email}.")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False
