from flask import url_for
from utils.brevo_mail import send_brevo_email


# Layout reutilizable
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


# EMAIL DE VERIFICACIÓN
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


# EMAIL DE CAMBIO DE EMAIL
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

def _full_name(name: str | None, surname: str | None) -> str:
    return f"{(name or '').strip()} {(surname or '').strip()}".strip()


def _exam_label(exam) -> str:
    parts = [f"Exam #{exam.id}"]
    if exam.class_exam and exam.class_exam.description:
        parts.append(f"for class {exam.class_exam.description}")
    return " ".join(parts)


def send_exam_on_review_email_to_teacher(exam) -> None:
    teacher = exam.user_exam
    coordinator = exam.coordinator_exam

    if not teacher or not teacher.email:
        return

    teacher_name = _full_name(teacher.name, teacher.surname) or "Teacher"
    coordinator_name = (
        _full_name(coordinator.name, coordinator.surname)
        if coordinator else "the coordinator"
    )
    exam_label = _exam_label(exam)

    content_html = f"""
    <p style="margin:0 0 24px 0;color:#6c757d;font-size:15px;line-height:1.6;">
      Your {exam_label} is now <strong>On Review</strong>.
    </p>

    <p style="margin:0 0 24px 0;color:#111111;font-size:15px;line-height:1.6;">
      It is currently being reviewed by <strong>{coordinator_name}</strong>.
    </p>
    """

    html = _build_email_layout(
        title="Exam under review",
        greeting=f"Hello {teacher_name},",
        content_html=content_html,
        footer="This is an automatic notification from IRI+.",
    )

    send_brevo_email(
        to_email=teacher.email,
        subject="IRI+ | Your exam is under review",
        html_content=html,
    )


def send_exam_sent_to_correction_email_to_teacher(exam) -> None:
    teacher = exam.user_exam
    coordinator = exam.coordinator_exam

    if not teacher or not teacher.email:
        return

    teacher_name = _full_name(teacher.name, teacher.surname) or "Teacher"
    coordinator_name = (
        _full_name(coordinator.name, coordinator.surname)
        if coordinator else "the coordinator"
    )
    exam_label = _exam_label(exam)

    notes_html = ""
    if exam.notes and exam.notes.strip():
        notes_html = f"""
        <div style="margin:16px 0;padding:14px;border-radius:10px;background:#f4efe2;">
          <p style="margin:0;color:#111111;font-size:14px;line-height:1.6;">
            <strong>Coordinator notes:</strong><br/>
            {exam.notes}
          </p>
        </div>
        """

    content_html = f"""
    <p style="margin:0 0 24px 0;color:#6c757d;font-size:15px;line-height:1.6;">
      Your {exam_label} was sent back for <strong>correction</strong>.
    </p>

    <p style="margin:0 0 24px 0;color:#111111;font-size:15px;line-height:1.6;">
      Requested by <strong>{coordinator_name}</strong>.
    </p>

    {notes_html}
    """

    html = _build_email_layout(
        title="Exam needs correction",
        greeting=f"Hello {teacher_name},",
        content_html=content_html,
        footer="This is an automatic notification from IRI+.",
    )

    send_brevo_email(
        to_email=teacher.email,
        subject="IRI+ | Your exam needs correction",
        html_content=html,
    )


def send_exam_corrected_email_to_coordinator(exam) -> None:
    coordinator = exam.coordinator_exam
    teacher = exam.user_exam

    if not coordinator or not coordinator.email:
        return

    coordinator_name = _full_name(coordinator.name, coordinator.surname) or "Coordinator"
    teacher_name = _full_name(teacher.name, teacher.surname) if teacher else "The teacher"
    exam_label = _exam_label(exam)

    content_html = f"""
    <p style="margin:0 0 24px 0;color:#6c757d;font-size:15px;line-height:1.6;">
      <strong>{teacher_name}</strong> submitted corrections for {exam_label}.
    </p>

    <p style="margin:0 0 24px 0;color:#111111;font-size:15px;line-height:1.6;">
      The exam is now <strong>Pending Review</strong> and ready to be reviewed again.
    </p>
    """

    html = _build_email_layout(
        title="Corrected exam ready for review",
        greeting=f"Hello {coordinator_name},",
        content_html=content_html,
        footer="This is an automatic notification from IRI+.",
    )

    send_brevo_email(
        to_email=coordinator.email,
        subject="IRI+ | A corrected exam is ready for review",
        html_content=html,
    )


def send_exam_accepted_email_to_teacher(exam) -> None:
    teacher = exam.user_exam
    coordinator = exam.coordinator_exam

    if not teacher or not teacher.email:
        return

    teacher_name = _full_name(teacher.name, teacher.surname) or "Teacher"
    coordinator_name = (
        _full_name(coordinator.name, coordinator.surname)
        if coordinator else "the coordinator"
    )
    exam_label = _exam_label(exam)

    content_html = f"""
    <p style="margin:0 0 24px 0;color:#6c757d;font-size:15px;line-height:1.6;">
      Your {exam_label} has been <strong>accepted</strong>.
    </p>

    <p style="margin:0 0 24px 0;color:#111111;font-size:15px;line-height:1.6;">
      Approved by <strong>{coordinator_name}</strong>.
    </p>
    """

    html = _build_email_layout(
        title="Exam accepted",
        greeting=f"Hello {teacher_name},",
        content_html=content_html,
        footer="This is an automatic notification from IRI+.",
    )

    send_brevo_email(
        to_email=teacher.email,
        subject="IRI+ | Your exam has been accepted",
        html_content=html,
    )