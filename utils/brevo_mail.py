import os
import requests

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

def send_brevo_email(to_email: str, subject: str, html_content: str) -> None:
    """Util for sending emails through the Brevo API"""
    api_key = os.getenv("BREVO_API_KEY")
    sender = os.getenv("MAIL_DEFAULT_SENDER")

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "sender": {"email": sender},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    r = requests.post(BREVO_URL, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
