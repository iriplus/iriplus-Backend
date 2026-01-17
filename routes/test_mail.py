import os
import requests
from flask import Blueprint, jsonify, current_app

test_mail_bp = Blueprint("test_mail", __name__)

@test_mail_bp.route("/api/test-mail", methods=["GET"])
def test_mail():
    """
    Send a test email via Brevo
    ---
    tags:
      - Utils
    summary: Send a test email using Brevo SMTP API
    description: |
      Sends a test email using the configured BREVO_API_KEY and MAIL_DEFAULT_SENDER
      environment variables. Useful to verify email delivery from the platform.

    responses:
      200:
        description: Request executed (does not guarantee email delivery)
        content:
          application/json:
            schema:
              type: object
              properties:
                status_code:
                  type: integer
                  description: HTTP status returned by Brevo
                response:
                  type: string
                  description: Raw response from Brevo API
                sender_used:
                  type: string
                  description: Email address used as sender
      500:
        description: Server error communicating with Brevo
    """
    api_key = os.getenv("BREVO_API_KEY")
    sender = os.getenv("MAIL_DEFAULT_SENDER")

    current_app.logger.info(f"BREVO_API_KEY exists: {bool(api_key)}")
    current_app.logger.info(f"SENDER: '{sender}'")

    url = "https://api.brevo.com/v3/smtp/email"

    payload = {
        "sender": {"email": sender},
        "to": [{"email": "dorigonimauro@gmail.com"}],
        "subject": "Brevo test",
        "htmlContent": "<p>Brevo + Render OK</p>",
    }

    headers = {
        "api-key": api_key.strip() if api_key else None,
        "Content-Type": "application/json",
    }

    r = requests.post(url, json=payload, headers=headers, timeout=10)

    return jsonify({
        "status_code": r.status_code,
        "response": r.text,
        "sender_used": sender,
    }), 200
