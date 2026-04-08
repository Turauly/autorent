import logging
import smtplib
from email.message import EmailMessage

from app.core.config import (
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_SSL,
    SMTP_USERNAME,
)

logger = logging.getLogger("autorent.email")


def send_verification_code(email: str, code: str) -> None:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST and SMTP_FROM_EMAIL.")

    msg = EmailMessage()
    msg["Subject"] = "AutoRent verification code"
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = email
    msg.set_content(f"Your AutoRent verification code is: {code}")

    try:
        use_ssl = SMTP_USE_SSL or SMTP_PORT == 465
        smtp_client = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_client(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            if not use_ssl:
                smtp.starttls()
            if SMTP_USERNAME:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception as exc:
        logger.exception("Failed to send verification code email")
        raise RuntimeError(f"Failed to send email: {exc}") from exc
