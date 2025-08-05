# notification_engine.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationEngine:
    def __init__(self, smtp_server, smtp_port, username, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_email(self, to_email, subject, message):
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            print(f"Email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def notify(self, event_type, details):
        subject = f"Notification: {event_type}"
        message = f"Details: {details}"
        # Example recipient, this could be dynamic based on the event
        recipient = "recipient@example.com"
        self.send_email(recipient, subject, message)