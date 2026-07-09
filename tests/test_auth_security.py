from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIRECTORY = ROOT / "app"

if str(APP_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(APP_DIRECTORY))

from backend.api.auth_security import (  # noqa: E402
    create_session_token,
    hash_password,
    hash_session_token,
    normalize_email,
    validate_password,
    verify_password,
)


class AuthSecurityTests(unittest.TestCase):
    def test_email_is_normalized(self):
        self.assertEqual(
            normalize_email(
                "  User@Example.COM "
            ),
            "user@example.com",
        )

    def test_password_hash_is_not_plaintext(self):
        password = "StrongPassword123"
        encoded = hash_password(password)

        self.assertNotEqual(encoded, password)
        self.assertTrue(
            encoded.startswith("scrypt$")
        )

    def test_correct_password_is_verified(self):
        password = "StrongPassword123"
        encoded = hash_password(password)

        self.assertTrue(
            verify_password(password, encoded)
        )

    def test_wrong_password_is_rejected(self):
        encoded = hash_password(
            "StrongPassword123"
        )

        self.assertFalse(
            verify_password(
                "IncorrectPassword123",
                encoded,
            )
        )

    def test_short_password_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_password("short1")

    def test_session_token_is_stored_as_hash(self):
        raw_token, token_hash = (
            create_session_token()
        )

        self.assertNotEqual(
            raw_token,
            token_hash,
        )

        self.assertEqual(
            hash_session_token(raw_token),
            token_hash,
        )


if __name__ == "__main__":
    unittest.main()
