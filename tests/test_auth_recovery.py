from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
APP_DIRECTORY = ROOT / "app"

if str(APP_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(APP_DIRECTORY))


os.environ.pop("DATABASE_URL", None)
os.environ.pop("RAILYATRA_DEMO_DATABASE_URL", None)
os.environ["RAILYATRA_ENV"] = "development"
os.environ["RAILYATRA_SESSION_COOKIE_SECURE"] = "false"
os.environ["RAILYATRA_AUTH_EMAIL_MODE"] = "disabled"

from tests.test_auth_api import (  # noqa: E402
    AUTH_TEST_DATABASE,
)

import backend.api.demo_store as demo_store  # noqa: E402

demo_store.DEMO_DB = AUTH_TEST_DATABASE

from fastapi.testclient import TestClient  # noqa: E402

from backend.api.auth_rate_limit import (  # noqa: E402
    reset_auth_rate_limits,
)
from backend.api.auth_recovery_rate_limit import (  # noqa: E402
    reset_auth_recovery_rate_limits,
)
from backend.api.main import app  # noqa: E402


client = TestClient(app)

TEST_EMAIL = "recovery@example.com"
TEST_PASSWORD = "StrongRailPassword123"
NEW_PASSWORD = "NewStrongRailPassword456"
TEST_NAME = "Recovery Traveller"


class AuthenticationRecoveryTests(unittest.TestCase):
    def setUp(self):
        client.cookies.clear()
        reset_auth_rate_limits()
        reset_auth_recovery_rate_limits()

        demo_store.DEMO_DB = AUTH_TEST_DATABASE

        if AUTH_TEST_DATABASE.exists():
            AUTH_TEST_DATABASE.unlink()

    def register_and_capture_verification_token(self) -> str:
        captured: dict[str, str] = {}

        def capture_email(
            email: str,
            display_name: str,
            raw_token: str,
        ) -> bool:
            captured["email"] = email
            captured["display_name"] = display_name
            captured["token"] = raw_token
            return True

        with patch(
            "backend.api.auth_api.send_verification_email",
            side_effect=capture_email,
        ):
            response = client.post(
                "/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "display_name": TEST_NAME,
                    "password": TEST_PASSWORD,
                },
            )

        self.assertEqual(
            response.status_code,
            201,
            response.text,
        )
        self.assertTrue(
            response.json()["verification_email_sent"]
        )
        self.assertEqual(captured["email"], TEST_EMAIL)

        return captured["token"]

    def test_email_verification_is_one_time(self):
        token = self.register_and_capture_verification_token()

        before = client.get(
            "/auth/email-verification/status"
        )
        self.assertEqual(before.status_code, 200)
        self.assertFalse(before.json()["email_verified"])

        confirm = client.post(
            "/auth/email-verification/confirm",
            json={"token": token},
        )
        self.assertEqual(
            confirm.status_code,
            200,
            confirm.text,
        )
        self.assertTrue(confirm.json()["email_verified"])

        after = client.get("/auth/me")
        self.assertEqual(after.status_code, 200)
        self.assertTrue(
            after.json()["user"]["email_verified"]
        )

        reused = client.post(
            "/auth/email-verification/confirm",
            json={"token": token},
        )
        self.assertEqual(reused.status_code, 400)

    def test_unknown_email_reset_is_not_disclosed(self):
        with patch(
            "backend.api.auth_api.send_password_reset_email"
        ) as mocked_email:
            response = client.post(
                "/auth/forgot-password",
                json={"email": "missing@example.com"},
            )

        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.json()["ok"])
        mocked_email.assert_not_called()

    def test_password_reset_revokes_sessions(self):
        self.register_and_capture_verification_token()
        captured: dict[str, str] = {}

        def capture_reset(
            email: str,
            display_name: str,
            raw_token: str,
        ) -> bool:
            captured["token"] = raw_token
            return True

        with patch(
            "backend.api.auth_api.send_password_reset_email",
            side_effect=capture_reset,
        ):
            request_reset = client.post(
                "/auth/forgot-password",
                json={"email": TEST_EMAIL},
            )

        self.assertEqual(
            request_reset.status_code,
            202,
            request_reset.text,
        )
        self.assertTrue(captured["token"])

        reset = client.post(
            "/auth/reset-password",
            json={
                "token": captured["token"],
                "new_password": NEW_PASSWORD,
            },
        )
        self.assertEqual(reset.status_code, 200, reset.text)

        after_reset = client.get("/auth/me")
        self.assertEqual(after_reset.status_code, 401)

        old_login = client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )
        self.assertEqual(old_login.status_code, 401)

        new_login = client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": NEW_PASSWORD,
            },
        )
        self.assertEqual(
            new_login.status_code,
            200,
            new_login.text,
        )

        reused = client.post(
            "/auth/reset-password",
            json={
                "token": captured["token"],
                "new_password": "AnotherStrongPassword789",
            },
        )
        self.assertEqual(reused.status_code, 400)


if __name__ == "__main__":
    unittest.main()
