from __future__ import annotations

import atexit
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIRECTORY = ROOT / "app"

if str(APP_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(APP_DIRECTORY))


# Never use the production PostgreSQL database during this test.
os.environ.pop("DATABASE_URL", None)
os.environ.pop("RAILYATRA_DEMO_DATABASE_URL", None)
os.environ["RAILYATRA_ENV"] = "development"
os.environ["RAILYATRA_SESSION_COOKIE_SECURE"] = "false"

_test_directory = tempfile.TemporaryDirectory()
atexit.register(_test_directory.cleanup)

AUTH_TEST_DATABASE = (
    Path(_test_directory.name)
    / "railyatra_auth_test.db"
)

import backend.api.demo_store as demo_store  # noqa: E402

demo_store.DEMO_DB = AUTH_TEST_DATABASE

from fastapi.testclient import TestClient  # noqa: E402

from backend.api.auth_security import (  # noqa: E402
    hash_session_token,
)
from backend.api.main import app  # noqa: E402


client = TestClient(app)

TEST_EMAIL = "traveller@example.com"
TEST_PASSWORD = "StrongRailPassword123"
TEST_NAME = "Rail Traveller"


class AuthenticationApiTests(unittest.TestCase):
    def setUp(self):
        client.cookies.clear()

        if AUTH_TEST_DATABASE.exists():
            AUTH_TEST_DATABASE.unlink()

    def register(self):
        return client.post(
            "/auth/register",
            json={
                "email": TEST_EMAIL,
                "display_name": TEST_NAME,
                "password": TEST_PASSWORD,
            },
        )

    def test_authentication_health(self):
        response = client.get("/auth/health")

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["service"],
            "authentication",
        )
        self.assertEqual(
            payload["storage"],
            "sqlite",
        )
        self.assertTrue(
            payload["supports_http_only_cookie"]
        )
        self.assertFalse(
            payload["raw_session_tokens_stored"]
        )

    def test_invalid_registration_is_rejected(self):
        response = client.post(
            "/auth/register",
            json={
                "email": "invalid-email",
                "display_name": "A",
                "password": "weak",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_complete_account_session_flow(self):
        register_response = self.register()

        self.assertEqual(
            register_response.status_code,
            201,
            register_response.text,
        )

        register_payload = register_response.json()

        self.assertTrue(register_payload["ok"])
        self.assertEqual(
            register_payload["user"]["email"],
            TEST_EMAIL,
        )
        self.assertNotIn(
            "password_hash",
            register_payload["user"],
        )

        set_cookie_header = register_response.headers.get(
            "set-cookie",
            "",
        ).lower()

        self.assertIn(
            "httponly",
            set_cookie_header,
        )

        raw_session_token = (
            register_response.cookies.get(
                "railyatra_session"
            )
        )

        self.assertTrue(raw_session_token)

        with sqlite3.connect(
            AUTH_TEST_DATABASE
        ) as database:
            user_row = database.execute(
                """
                SELECT password_hash
                FROM users
                WHERE email = ?
                """,
                (TEST_EMAIL,),
            ).fetchone()

            session_row = database.execute(
                """
                SELECT token_hash
                FROM user_sessions
                LIMIT 1
                """
            ).fetchone()

        self.assertIsNotNone(user_row)
        self.assertIsNotNone(session_row)

        stored_password_hash = user_row[0]
        stored_token_hash = session_row[0]

        self.assertNotEqual(
            stored_password_hash,
            TEST_PASSWORD,
        )
        self.assertTrue(
            stored_password_hash.startswith("scrypt$")
        )

        self.assertNotEqual(
            stored_token_hash,
            raw_session_token,
        )
        self.assertEqual(
            stored_token_hash,
            hash_session_token(raw_session_token),
        )

        me_response = client.get("/auth/me")

        self.assertEqual(
            me_response.status_code,
            200,
            me_response.text,
        )
        self.assertEqual(
            me_response.json()["user"]["email"],
            TEST_EMAIL,
        )

        duplicate_response = self.register()

        self.assertEqual(
            duplicate_response.status_code,
            409,
        )

        logout_response = client.post(
            "/auth/logout"
        )

        self.assertEqual(
            logout_response.status_code,
            200,
        )
        self.assertTrue(
            logout_response.json()[
                "session_revoked"
            ]
        )

        after_logout_response = client.get(
            "/auth/me"
        )

        self.assertEqual(
            after_logout_response.status_code,
            401,
        )

        invalid_login = client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": "WrongPassword123",
            },
        )

        self.assertEqual(
            invalid_login.status_code,
            401,
        )

        login_response = client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        self.assertEqual(
            login_response.status_code,
            200,
            login_response.text,
        )
        self.assertTrue(
            login_response.json()["ok"]
        )

        final_me_response = client.get(
            "/auth/me"
        )

        self.assertEqual(
            final_me_response.status_code,
            200,
        )
        self.assertEqual(
            final_me_response.json()[
                "user"
            ]["display_name"],
            TEST_NAME,
        )


    def test_saved_journeys_require_authentication(self):
        response = client.get(
            "/account/saved-journeys"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_saved_journey_create_list_upsert_delete(self):
        self.register()

        create_response = client.post(
            "/account/saved-journeys",
            json={
                "source": "pnbe",
                "destination": "ndls",
                "journey_date": "2026-08-01",
                "class_code": "3A",
                "quota": "GN",
                "label": "Patna to Delhi",
                "note": "Family journey",
            },
        )

        self.assertEqual(
            create_response.status_code,
            201,
            create_response.text,
        )

        created = create_response.json()[
            "journey"
        ]

        self.assertEqual(
            created["source"],
            "PNBE",
        )
        self.assertEqual(
            created["destination"],
            "NDLS",
        )

        update_response = client.post(
            "/account/saved-journeys",
            json={
                "source": "PNBE",
                "destination": "NDLS",
                "journey_date": "2026-08-01",
                "class_code": "3A",
                "quota": "GN",
                "label": "Updated Delhi trip",
            },
        )

        self.assertEqual(
            update_response.status_code,
            201,
        )
        self.assertEqual(
            update_response.json()[
                "journey"
            ]["id"],
            created["id"],
        )

        list_response = client.get(
            "/account/saved-journeys"
        )

        self.assertEqual(
            list_response.status_code,
            200,
        )
        self.assertEqual(
            list_response.json()["count"],
            1,
        )
        self.assertEqual(
            list_response.json()[
                "journeys"
            ][0]["label"],
            "Updated Delhi trip",
        )

        delete_response = client.delete(
            (
                "/account/saved-journeys/"
                f"{created['id']}"
            )
        )

        self.assertEqual(
            delete_response.status_code,
            200,
        )

        empty_response = client.get(
            "/account/saved-journeys"
        )

        self.assertEqual(
            empty_response.json()["count"],
            0,
        )

    def test_saved_journey_import_deduplicates(self):
        self.register()

        response = client.post(
            "/account/saved-journeys/import",
            json={
                "journeys": [
                    {
                        "source": "PNBE",
                        "destination": "NDLS",
                        "label": "First label",
                    },
                    {
                        "source": "PNBE",
                        "destination": "NDLS",
                        "label": "Latest label",
                    },
                    {
                        "source": "LTT",
                        "destination": "VVH",
                        "label": "Mumbai route",
                    },
                ]
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )
        self.assertEqual(
            response.json()["processed_count"],
            3,
        )
        self.assertEqual(
            response.json()["account_count"],
            2,
        )

        labels = {
            item["label"]
            for item in response.json()["journeys"]
        }

        self.assertIn(
            "Latest label",
            labels,
        )

    def test_saved_journey_ownership_is_enforced(self):
        self.register()

        create_response = client.post(
            "/account/saved-journeys",
            json={
                "source": "PNBE",
                "destination": "NDLS",
            },
        )

        journey_id = create_response.json()[
            "journey"
        ]["id"]

        client.cookies.clear()

        second_register = client.post(
            "/auth/register",
            json={
                "email": "second@example.com",
                "display_name": "Second Traveller",
                "password": "SecondPassword123",
            },
        )

        self.assertEqual(
            second_register.status_code,
            201,
        )

        forbidden_delete = client.delete(
            (
                "/account/saved-journeys/"
                f"{journey_id}"
            )
        )

        self.assertEqual(
            forbidden_delete.status_code,
            404,
        )

        second_user_list = client.get(
            "/account/saved-journeys"
        )

        self.assertEqual(
            second_user_list.json()["count"],
            0,
        )

    def test_untrusted_write_origin_is_rejected(self):
        self.register()

        response = client.post(
            "/account/saved-journeys",
            headers={
                "Origin": "https://evil.example"
            },
            json={
                "source": "PNBE",
                "destination": "NDLS",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )


    def test_change_password_rotates_all_sessions(self):
        self.register()

        second_client = TestClient(app)
        second_login = second_client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        self.assertEqual(
            second_login.status_code,
            200,
            second_login.text,
        )

        old_token = client.cookies.get(
            "railyatra_session"
        )
        new_password = "NewStrongRailPassword456"

        response = client.post(
            "/auth/change-password",
            json={
                "current_password": TEST_PASSWORD,
                "new_password": new_password,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )
        self.assertTrue(
            response.json()["sessions_revoked"] >= 2
        )

        new_token = client.cookies.get(
            "railyatra_session"
        )

        self.assertTrue(new_token)
        self.assertNotEqual(old_token, new_token)
        self.assertEqual(
            client.get("/auth/me").status_code,
            200,
        )
        self.assertEqual(
            second_client.get("/auth/me").status_code,
            401,
        )

        old_password_client = TestClient(app)
        old_login = old_password_client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )
        self.assertEqual(old_login.status_code, 401)

        new_password_client = TestClient(app)
        new_login = new_password_client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": new_password,
            },
        )
        self.assertEqual(
            new_login.status_code,
            200,
            new_login.text,
        )

    def test_logout_all_revokes_every_session(self):
        self.register()

        second_client = TestClient(app)
        second_login = second_client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )
        self.assertEqual(second_login.status_code, 200)

        response = client.post("/auth/logout-all")

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )
        self.assertTrue(
            response.json()["sessions_revoked"] >= 2
        )
        self.assertEqual(
            client.get("/auth/me").status_code,
            401,
        )
        self.assertEqual(
            second_client.get("/auth/me").status_code,
            401,
        )

    def test_account_deletion_requires_confirmation_and_cascades(self):
        self.register()

        saved_response = client.post(
            "/account/saved-journeys",
            json={
                "source": "PNBE",
                "destination": "NDLS",
                "journey_date": "2026-08-01",
                "class_code": "SL",
                "quota": "GN",
                "label": "Deletion test",
                "note": "",
            },
        )
        self.assertEqual(
            saved_response.status_code,
            201,
            saved_response.text,
        )

        invalid_confirmation = client.request(
            "DELETE",
            "/auth/account",
            json={
                "password": TEST_PASSWORD,
                "confirmation": "delete",
            },
        )
        self.assertEqual(
            invalid_confirmation.status_code,
            422,
        )

        wrong_password = client.request(
            "DELETE",
            "/auth/account",
            json={
                "password": "WrongPassword123",
                "confirmation": "DELETE MY ACCOUNT",
            },
        )
        self.assertEqual(
            wrong_password.status_code,
            401,
        )

        response = client.request(
            "DELETE",
            "/auth/account",
            json={
                "password": TEST_PASSWORD,
                "confirmation": "DELETE MY ACCOUNT",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )
        self.assertTrue(
            response.json()["account_deleted"]
        )
        self.assertEqual(
            client.get("/auth/me").status_code,
            401,
        )

        failed_login = client.post(
            "/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )
        self.assertEqual(failed_login.status_code, 401)

        with sqlite3.connect(
            AUTH_TEST_DATABASE
        ) as database:
            user_count = database.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]
            session_count = database.execute(
                "SELECT COUNT(*) FROM user_sessions"
            ).fetchone()[0]
            journey_count = database.execute(
                "SELECT COUNT(*) FROM saved_journeys"
            ).fetchone()[0]

        self.assertEqual(user_count, 0)
        self.assertEqual(session_count, 0)
        self.assertEqual(journey_count, 0)

    def test_untrusted_auth_security_origin_is_rejected(self):
        self.register()

        response = client.post(
            "/auth/logout-all",
            headers={
                "Origin": "https://malicious.example",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            client.get("/auth/me").status_code,
            200,
        )


if __name__ == "__main__":
    unittest.main()
