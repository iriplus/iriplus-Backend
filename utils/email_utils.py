from flask import url_for
from utils.brevo_mail import send_brevo_email


# 🔧 Layout reutilizable
def _build_email_layout(
    title: str,
    greeting: str,
    content_html: str,
    footer: str,
) -> str:
    return f"""
    <div style="background-color:#1E2A22;padding:36px 20px;font-family:'Segoe UI',sans-serif;">
      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:640px;margin:0 auto;background:#FCFAF4;border-radius:14px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.30);">
        
        <!-- LOGO -->
        <tr>
          <td style="padding:32px 32px 0 32px;">
            <img 
              src="https://drive.google.com/uc?export=view&id=19gasS21wL7qLPAE3wqebD1Ks2zXHLlCm"
              width="56"
              height="56"
              style="display:block;"
              alt="IRI+ Logo"
            />
          </td>
        </tr>

        <!-- CONTENIDO -->
        <tr>
          <td style="padding:20px 32px 0 32px;">
            <h1 style="margin:0 0 10px 0;color:#1a3a21;font-size:26px;font-weight:700;">
              {title}
            </h1>

            <p style="margin:0 0 14px 0;color:#111111;font-size:16px;line-height:1.6;">
              {greeting}
            </p>

            {content_html}
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="padding:28px 32px 32px 32px;">
            <p style="margin:16px 0 0 0;color:#6c757d;font-size:13px;line-height:1.6;">
              {footer}
            </p>
          </td>
        </tr>

      </table>
    </div>
    """


# 📧 EMAIL DE VERIFICACIÓN
def send_welcome_email(email: str, name: str, token: str):
    verification_link = url_for("auth.verify", token=token, _external=True)

    content_html = f"""
    <p style="margin:0 0 24px 0;color:#6c757d;font-size:15px;line-height:1.6;">
      ¡Welcome to IRI+! To activate your account, click on the button.
    </p>

    <a href="{verification_link}" style="display:inline-block;background:linear-gradient(135deg,#27532f,#1a3a21);color:#ffffff;text-decoration:none;padding:12px 22px;border-radius:999px;font-weight:600;font-size:15px;">
      Verify my email
    </a>
    """

    html = _build_email_layout(
        title="Verify your email",
        greeting=f"Hi {name},",
        content_html=content_html,
        footer="If you haven't created an account, you can ignore this email.",
    )

    send_brevo_email(
        to_email=email,
        subject="Welcome to IRI+! Verify your email",
        html_content=html,
    )


# 📧 EMAIL DE CAMBIO DE EMAIL
def send_email_change_verification_email(email: str, name: str, token: str) -> None:
    verification_link = url_for("auth.verify", token=token, _external=True)

    content_html = f"""
    <p style="margin:0 0 24px 0;color:#6c757d;font-size:15px;line-height:1.6;">
      We received a request to change your email address.
    </p>

    <a href="{verification_link}" style="display:inline-block;background:linear-gradient(135deg,#27532f,#1a3a21);color:#ffffff;text-decoration:none;padding:12px 22px;border-radius:999px;font-weight:600;font-size:15px;">
      Verify my new email
    </a>
    """

    html = _build_email_layout(
        title="Verify your new email",
        greeting=f"Hello {name},",
        content_html=content_html,
        footer="If you did not request this change, you can ignore this email.",
    )

    send_brevo_email(
        to_email=email,
        subject="IRI+ | Verify your new email address",
        html_content=html,
    )