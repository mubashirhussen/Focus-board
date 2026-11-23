import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from app.core.config import settings

logger = logging.getLogger("focusboard.email")

class EmailService:
    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.sender_email = settings.EMAIL_FROM
        self.sender_name = getattr(settings, "SMTP_FROM_NAME", "FocusBoard")
        self.use_tls = getattr(settings, "SMTP_USE_TLS", True)
        self.use_ssl = getattr(settings, "SMTP_USE_SSL", False)

    @property
    def sender_header(self) -> str:
        return formataddr((self.sender_name, self.sender_email))

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
            msg["From"] = self.sender_header
            msg["To"] = to_email

            part = MIMEText(message, "plain")
            msg.attach(part)

            self._send_via_smtp(msg, to_email)
            logger.info(f"Notification email sent successfully to {to_email}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to deliver notification email to {to_email}: {exc}")
            return False

    def send_otp_email(self, to_email: str, otp: str, purpose: str = "login", expires_minutes: int = 5) -> bool:
        """
        Dispatches a cryptographically secure 6-digit OTP verification email
        with responsive HTML and plain-text alternatives.
        """
        purpose_label = "Account Registration" if purpose == "registration" else "Sign In"
        subject = f"{otp} is your FocusBoard verification code"

        plain_text = f"""FocusBoard Email Verification

Your verification code is: {otp}

This code expires in {expires_minutes} minutes.
Enter this 6-digit code on the FocusBoard verification screen to complete your {purpose_label.lower()}.

Security Notice: If you did not request this verification code, you can safely ignore this email.
Never share your verification code with anyone. FocusBoard team members will never ask for it.
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FocusBoard Verification Code</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; margin: 0; padding: 24px; color: #f1f5f9; }}
    .container {{ max-width: 540px; margin: 0 auto; background: #131b2e; border: 1px solid #1e293b; border-radius: 14px; overflow: hidden; }}
    .header {{ padding: 28px 32px 20px; border-bottom: 1px solid #1e293b; display: flex; align-items: center; gap: 12px; }}
    .logo-badge {{ display: inline-block; width: 28px; height: 28px; border-radius: 8px; background: linear-gradient(135deg, #6366f1, #8b5cf6); text-align: center; line-height: 28px; font-weight: bold; color: #fff; }}
    .brand-title {{ font-size: 19px; font-weight: 700; color: #ffffff; letter-spacing: -0.02em; }}
    .content {{ padding: 32px; }}
    .greeting {{ font-size: 15px; color: #94a3b8; margin-bottom: 8px; }}
    .title {{ font-size: 22px; font-weight: 700; color: #ffffff; margin: 0 0 16px; line-height: 1.3; }}
    .desc {{ font-size: 14px; color: #cbd5e1; line-height: 1.5; margin-bottom: 24px; }}
    .otp-box {{ background: #0b0f19; border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0; }}
    .otp-code {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; font-size: 34px; font-weight: 700; letter-spacing: 8px; color: #818cf8; }}
    .expiry {{ font-size: 13px; color: #94a3b8; margin-top: 8px; }}
    .security-note {{ font-size: 12px; color: #64748b; line-height: 1.5; border-top: 1px solid #1e293b; padding-top: 20px; margin-top: 24px; }}
    .footer {{ background: #0b0f19; padding: 20px 32px; font-size: 12px; color: #475569; text-align: center; border-top: 1px solid #1e293b; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="logo-badge">F</span>
      <span class="brand-title">FocusBoard</span>
    </div>
    <div class="content">
      <div class="greeting">Hello,</div>
      <h1 class="title">{purpose_label} Verification</h1>
      <p class="desc">Enter the single-use 6-digit code below to securely authenticate your email address:</p>
      
      <div class="otp-box">
        <div class="otp-code">{otp}</div>
        <div class="expiry">This verification code expires in <strong>{expires_minutes} minutes</strong>.</div>
      </div>
      
      <p class="desc">If you did not request this verification code, someone may have entered your email address by mistake. You can safely disregard this message.</p>
      
      <div class="security-note">
        <strong>Security Warning:</strong> Never share your verification code or account credentials with anyone. FocusBoard staff will never ask for your code.
      </div>
    </div>
    <div class="footer">
      &copy; 2026 FocusBoard Inc. All rights reserved. &bull; Enterprise Grade Productivity
    </div>
  </div>
</body>
</html>"""

        if not self.enabled:
            logger.info(f"[Email Mock/Disabled] To: {to_email} | Purpose: {purpose} | OTP: {otp} | Expires: {expires_minutes}m")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_header
            msg["To"] = to_email

            part1 = MIMEText(plain_text, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            self._send_via_smtp(msg, to_email)
            logger.info(f"OTP verification email successfully delivered to {to_email} (purpose={purpose})")
            return True
        except Exception as exc:
            logger.warning(f"Failed to deliver OTP email to {to_email}: {exc}")
            return False

    def _send_via_smtp(self, msg: MIMEMultipart, to_email: str):
        """Internal SMTP dispatch helper with SSL/TLS support."""
        if self.use_ssl:
            with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.sender_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.sender_email, [to_email], msg.as_string())

email_service = EmailService()
