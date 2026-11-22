import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger("focusboard.email")

class EmailService:
    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.sender = settings.EMAIL_FROM

    def send_notification_email(self, to_email: str, subject: str, message: str) -> bool:
        """
        Send a notification email.
        If email is not enabled or credentials are mock, logs cleanly and returns True without failing.
        """
        if not self.enabled:
            logger.info(f"[Email Mock/Disabled] To: {to_email} | Subject: {subject} | Body: {message}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = to_email

            part = MIMEText(message, "plain")
            msg.attach(part)

            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.sender, [to_email], msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to deliver email to {to_email}: {exc}")
            return False

email_service = EmailService()
