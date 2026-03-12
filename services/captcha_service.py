import os
import requests


def verify_captcha(token: str) -> bool:
    """
    Verify reCAPTCHA token with Google.
    Returns True if valid, False otherwise.
    """

    secret = os.getenv("RECAPTCHA_SECRET_KEY")

    if not secret or not token:
        return False

    try:
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": secret,
                "response": token
            },
            timeout=5
        )

        result = response.json()
        return result.get("success", False)

    except requests.RequestException:
        return False