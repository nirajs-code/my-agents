import os
import smtplib
from email.mime.text import MIMEText

def send_email(text):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_to = os.getenv("GMAIL_TO")
    msg = MIMEText(text)
    msg['Subject'] = 'Notification from My Agents'
    msg['From'] = gmail_user
    msg['To'] = gmail_to
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(gmail_user, os.getenv("GMAIL_APP_PASSWORD"))
        server.sendmail(gmail_user, gmail_to, msg.as_string())
        print("Notification sent successfully.")
