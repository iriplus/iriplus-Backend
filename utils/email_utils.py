from flask import url_for
from utils.brevo_mail import send_brevo_email

def send_welcome_email(email: str, name: str, token: str):
    """Util for sending verification emails when user does the signup"""
    verification_link = url_for("auth.verify", token=token, _external=True)

    html = f"""
    <p>Hola {name},</p>
    <p>¡Bienvenido a IRI+!</p>
    <p>Para activar tu cuenta hacé clic aquí:</p>
    <p><a href="{verification_link}">Verificar mi correo</a></p>
    <p>Si no creaste una cuenta, podés ignorar este correo.</p>
    """

    send_brevo_email(
        to_email=email,
        subject="¡Bienvenido a IRI+! Verificá tu correo",
        html_content=html,
    )

def send_email_change_verification_email(email: str, name: str, token: str) -> None:
    """Send a verification email after the user changes their email address."""
    verification_link = url_for("auth.verify", token=token, _external=True)

    html = f"""
    <p>Hello {name},</p>
    <p>We received a request to change the email address associated with your IRI+ account.</p>
    <p>Please confirm your new email by clicking the link below:</p>
    <p><a href="{verification_link}">Verify my new email</a></p>
    <p>If you did not request this change, you can ignore this email.</p>
    """

    send_brevo_email(
        to_email=email,
        subject="IRI+ | Verify your new email address",
        html_content=html,
    )
