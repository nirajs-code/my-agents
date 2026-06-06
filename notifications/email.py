import os
import smtplib
import structlog
from email.mime.text import MIMEText

log = structlog.get_logger()

def send_email(text):
    try:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_to = os.getenv("GMAIL_TO")
        msg = MIMEText(text)
        msg['Subject'] = 'Notification from My Agents'
        msg['From'] = gmail_user
        msg['To'] = gmail_to
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, os.getenv("GMAIL_APP_PASSWORD"))
            server.sendmail(gmail_user, gmail_to, msg.as_string())
            log.info("email_sent", to=gmail_to)
    except Exception as e:
        log.error("email_failed", error=str(e))
        raise
