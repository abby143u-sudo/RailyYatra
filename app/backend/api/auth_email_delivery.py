from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from urllib.parse import quote


def email_delivery_mode() -> str:
    mode = os.environ.get(
        "RAILYATRA_AUTH_EMAIL_MODE",
        "disabled",
    ).strip().lower()

    if mode not in {"disabled", "stdout", "smtp"}:
        return "disabled"

    return mode


def frontend_base_url() -> str:
    return (
        os.environ.get(
            "RAILYATRA_FRONTEND_URL",
            "http://localhost:5173",
        ).strip().rstrip("/")
        or "http://localhost:5173"
    )


def _smtp_send(
    recipient: str,
    subject: str,
    body: str,
) -> bool:
    host = os.environ.get("RAILYATRA_SMTP_HOST", "").strip()
    port = int(os.environ.get("RAILYATRA_SMTP_PORT", "587"))
    username = os.environ.get(
        "RAILYATRA_SMTP_USERNAME",
        "",
    ).strip()
    password = os.environ.get(
        "RAILYATRA_SMTP_PASSWORD",
        "",
    )
    sender = os.environ.get(
        "RAILYATRA_AUTH_EMAIL_FROM",
        username,
    ).strip()
    use_tls = os.environ.get(
        "RAILYATRA_SMTP_USE_TLS",
        "true",
    ).strip().lower() == "true"

    if not host or not sender:
        return False

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as client:
            if use_tls:
                client.starttls()
            if username:
                client.login(username, password)
            client.send_message(message)
    except Exception as error:
        print(
            "RailBay authentication email delivery failed: "
            f"{type(error).__name__}"
        )
        return False

    return True


def _deliver(
    recipient: str,
    subject: str,
    body: str,
) -> bool:
    mode = email_delivery_mode()

    if mode == "disabled":
        return False

    if mode == "stdout":
        print(
            "\n===== RailBay authentication email =====\n"
            f"To: {recipient}\n"
            f"Subject: {subject}\n\n"
            f"{body}\n"
            "===========================================\n"
        )
        return True

    return _smtp_send(recipient, subject, body)


def send_verification_email(
    email: str,
    display_name: str,
    raw_token: str,
) -> bool:
    link = (
        f"{frontend_base_url()}/verify-email"
        f"?token={quote(raw_token, safe='')}"
    )
    body = (
        f"Hello {display_name},\n\n"
        "Verify your RailBay email address using this link:\n"
        f"{link}\n\n"
        "This link expires automatically. If you did not create "
        "this account, you can ignore this email."
    )

    return _deliver(
        email,
        "Verify your RailBay email",
        body,
    )


def send_password_reset_email(
    email: str,
    display_name: str,
    raw_token: str,
) -> bool:
    link = (
        f"{frontend_base_url()}/reset-password"
        f"?token={quote(raw_token, safe='')}"
    )
    body = (
        f"Hello {display_name},\n\n"
        "Reset your RailBay password using this link:\n"
        f"{link}\n\n"
        "This link expires automatically and can be used only "
        "once. If you did not request a reset, ignore this email."
    )

    return _deliver(
        email,
        "Reset your RailBay password",
        body,
    )
