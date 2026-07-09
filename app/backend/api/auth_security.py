from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets


EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_LENGTH = 32


def normalize_email(value: str) -> str:
    email = str(value or "").strip().casefold()

    if not email:
        raise ValueError("Email is required.")

    if len(email) > 254:
        raise ValueError("Email is too long.")

    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("Enter a valid email address.")

    return email


def normalize_display_name(value: str) -> str:
    display_name = " ".join(
        str(value or "").strip().split()
    )

    if len(display_name) < 2:
        raise ValueError(
            "Display name must contain at least 2 characters."
        )

    if len(display_name) > 80:
        raise ValueError(
            "Display name must not exceed 80 characters."
        )

    return display_name


def validate_password(password: str) -> str:
    value = str(password or "")

    if len(value) < 10:
        raise ValueError(
            "Password must contain at least 10 characters."
        )

    if len(value) > 128:
        raise ValueError(
            "Password must not exceed 128 characters."
        )

    if not any(character.isalpha() for character in value):
        raise ValueError(
            "Password must contain at least one letter."
        )

    if not any(character.isdigit() for character in value):
        raise ValueError(
            "Password must contain at least one number."
        )

    return value


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(
        value.encode("ascii")
    )


def hash_password(password: str) -> str:
    validated = validate_password(password)
    salt = secrets.token_bytes(16)

    derived = hashlib.scrypt(
        validated.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_LENGTH,
    )

    return (
        f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}$"
        f"{_encode(salt)}${_encode(derived)}"
    )


def verify_password(
    password: str,
    encoded_password: str,
) -> bool:
    try:
        (
            algorithm,
            n_value,
            r_value,
            p_value,
            salt_value,
            hash_value,
        ) = encoded_password.split("$", 5)

        if algorithm != "scrypt":
            return False

        expected_hash = _decode(hash_value)

        actual_hash = hashlib.scrypt(
            str(password or "").encode("utf-8"),
            salt=_decode(salt_value),
            n=int(n_value),
            r=int(r_value),
            p=int(p_value),
            dklen=len(expected_hash),
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash,
        )
    except (
        ValueError,
        TypeError,
        OverflowError,
    ):
        return False


def hash_session_token(token: str) -> str:
    return hashlib.sha256(
        str(token or "").encode("utf-8")
    ).hexdigest()


def create_session_token() -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(32)

    return (
        raw_token,
        hash_session_token(raw_token),
    )
