"""
Email utility functions for sending user-facing emails such as account
activation links and welcome messages.
"""
from flask_mail import Message
from flask import url_for
from extensions.mail_extension import mail

def send_welcome_email(email: str, name: str, token: str):
    """
    Send a welcome email including an account verification link.

    Args:
        email: Recipient email address.
        name: User's display name used in the email body.
        token: Email verification token included in the activation URL.

    The function resolves the verification route using Flask's url_for
    and sends a simple text email using Flask-Mail.
    """
    verification_link = url_for("auth.verify", token=token, _external=True)
    body = (
        f"Hola {name},\n\n"
        "¡Bienvenido a IRI+!\n"
        "Para activar tu cuenta hacé clic en el siguiente enlace:\n\n"
        f"{verification_link}\n\n"
        "Si no creaste una cuenta, podés ignorar este correo."
    )

    msg = Message(
        subject="¡Bienvenido a IRI+! Verificá tu correo",
        recipients=[email],
        body=body
    )
    mail.send(msg)
