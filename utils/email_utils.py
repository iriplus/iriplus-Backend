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
