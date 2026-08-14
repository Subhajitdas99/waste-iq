import smtplib
from email.message import EmailMessage

from app.core.config import settings

def send_password_reset_email(email: str, token: str) -> None:
    """
    Sends a password reset email using SMTP.
    """
    reset_link = f"http://localhost:5173/reset-password?token={token}"

    host = settings.smtp_host
    user = settings.smtp_user
    password = settings.smtp_password
    from_email = settings.emails_from_email

    if not host or not user or not password or not from_email:
        print(f"\n[EMAIL MOCK - MISSING CONFIG] Password Reset Link for {email}:\n{reset_link}\n")
        return

    msg = EmailMessage()
    msg.set_content(
        f"Click the following link to reset your Waste-IQ password:\n\n"
        f"{reset_link}\n\n"
        f"If you did not request this, please ignore this email."
    )
    msg["Subject"] = "Waste-IQ Password Reset"
    msg["From"] = from_email
    msg["To"] = email

    try:
        with smtplib.SMTP(host, settings.smtp_port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        print(f"Successfully sent password reset email to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
