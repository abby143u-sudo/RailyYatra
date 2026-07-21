from __future__ import annotations

import json
import os
import smtplib
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


RESEND_API_URL = "https://api.resend.com/emails"


def email_delivery_mode() -> str:
    mode = os.environ.get(
        "RAILYATRA_AUTH_EMAIL_MODE",
        "disabled",
    ).strip().lower()

    if mode not in {
        "disabled",
        "stdout",
        "smtp",
        "resend",
    }:
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


def configured_sender() -> str:
    return os.environ.get(
        "RAILYATRA_AUTH_EMAIL_FROM",
        "",
    ).strip()


def _smtp_send(
    recipient: str,
    subject: str,
    body: str,
) -> bool:
    host = os.environ.get(
        "RAILYATRA_SMTP_HOST",
        "",
    ).strip()

    try:
        port = int(
            os.environ.get(
                "RAILYATRA_SMTP_PORT",
                "587",
            )
        )
    except ValueError:
        port = 587

    username = os.environ.get(
        "RAILYATRA_SMTP_USERNAME",
        "",
    ).strip()
    password = os.environ.get(
        "RAILYATRA_SMTP_PASSWORD",
        "",
    )
    sender = configured_sender() or username
    use_tls = (
        os.environ.get(
            "RAILYATRA_SMTP_USE_TLS",
            "true",
        ).strip().lower()
        == "true"
    )

    if not host or not sender:
        return False

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(
            host,
            port,
            timeout=15,
        ) as client:
            if use_tls:
                client.starttls()

            if username:
                client.login(
                    username,
                    password,
                )

            client.send_message(message)

    except Exception as error:
        print(
            "RailBay authentication email delivery failed: "
            f"{type(error).__name__}"
        )
        return False

    return True


def _resend_send(
    recipient: str,
    subject: str,
    body: str,
) -> bool:
    api_key = os.environ.get(
        "RAILYATRA_RESEND_API_KEY",
        "",
    ).strip()
    sender = configured_sender()

    if not api_key or not sender:
        print(
            "RailBay Resend email configuration is incomplete."
        )
        return False

    payload = {
        "from": sender,
        "to": [recipient],
        "subject": subject,
        "text": body,
    }

    request = Request(
        RESEND_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "RailBay/1.0",
        },
    )

    try:
        with urlopen(
            request,
            timeout=15,
        ) as response:
            status_code = int(
                getattr(response, "status", 0)
            )
            response.read()

        if 200 <= status_code < 300:
            return True

        print(
            "RailBay authentication email delivery failed: "
            f"Resend HTTP {status_code}"
        )
        return False

    except HTTPError as error:
        print(
            "RailBay authentication email delivery failed: "
            f"Resend HTTP {error.code}"
        )
    except (
        URLError,
        OSError,
        TimeoutError,
    ) as error:
        print(
            "RailBay authentication email delivery failed: "
            f"{type(error).__name__}"
        )

    return False


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

    if mode == "resend":
        return _resend_send(
            recipient,
            subject,
            body,
        )

    return _smtp_send(
        recipient,
        subject,
        body,
    )


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
