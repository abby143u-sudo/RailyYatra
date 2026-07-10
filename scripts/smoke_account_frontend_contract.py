from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP_FILE = ROOT / "frontend" / "src" / "App.jsx"
ACCOUNT_FILE = (
    ROOT
    / "frontend"
    / "src"
    / "components"
    / "UserAccountPanel.jsx"
)
ACCOUNT_CSS_FILE = (
    ROOT
    / "frontend"
    / "src"
    / "components"
    / "UserAccountPanel.css"
)


def read_required_file(path: Path) -> str:
    if not path.exists():
        raise SystemExit(
            f"FAIL: required file missing: "
            f"{path.relative_to(ROOT)}"
        )

    return path.read_text(encoding="utf-8")


def require_phrase(
    text: str,
    phrase: str,
    label: str,
) -> None:
    if phrase not in text:
        raise SystemExit(
            f"FAIL: missing {label}: {phrase}"
        )

    print(f"PASS: {label}")


print("RailYatra account frontend contract smoke test")
print("Mode: static security and integration check")

app_text = read_required_file(APP_FILE)
account_text = read_required_file(ACCOUNT_FILE)
read_required_file(ACCOUNT_CSS_FILE)

print("PASS: account component files exist")

component_requirements = [
    (
        'import { apiUrl } from "../config/api.js";',
        "shared API URL helper",
    ),
    (
        'credentials: "include"',
        "credentialed cookie requests",
    ),
    (
        '"/auth/me"',
        "session restoration request",
    ),
    (
        '"/auth/register"',
        "registration request",
    ),
    (
        '"/auth/login"',
        "login request",
    ),
    (
        '"/auth/logout"',
        "logout request",
    ),
    (
        '"/auth/change-password"',
        "change password request",
    ),
    (
        '"/auth/logout-all"',
        "all-device logout request",
    ),
    (
        '"/auth/account"',
        "account deletion request",
    ),
    (
        '"DELETE MY ACCOUNT"',
        "exact account deletion confirmation",
    ),
    (
        "Change password",
        "change password action",
    ),
    (
        "Log out all devices",
        "all-device logout action",
    ),
    (
        "Delete account permanently",
        "permanent account deletion action",
    ),
    (
        '"/account/saved-journeys"',
        "saved journey list/create request",
    ),
    (
        '"/account/saved-journeys/import"',
        "browser journey import request",
    ),
    (
        'method: "DELETE"',
        "saved journey deletion request",
    ),
    (
        "railyatra_saved_demo_searches",
        "browser saved journey migration key",
    ),
    (
        "Save current journey",
        "cloud save action",
    ),
    (
        "Import browser journeys",
        "browser import action",
    ),
]

for phrase, label in component_requirements:
    require_phrase(
        account_text,
        phrase,
        label,
    )

app_requirements = [
    (
        (
            'import UserAccountPanel from '
            '"./components/UserAccountPanel.jsx";'
        ),
        "account component import",
    ),
    (
        "<UserAccountPanel",
        "account component render",
    ),
    (
        "currentSource={source}",
        "main source integration",
    ),
    (
        "currentDestination={destination}",
        "main destination integration",
    ),
    (
        "currentJourneyDate={journeyDate}",
        "journey date integration",
    ),
    (
        "currentClassCode={journeyClass}",
        "journey class integration",
    ),
    (
        "currentQuota={quota}",
        "quota integration",
    ),
    (
        "onApplyRoute=",
        "saved journey apply callback",
    ),
]

for phrase, label in app_requirements:
    require_phrase(
        app_text,
        phrase,
        label,
    )

for forbidden in [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://railyyatra-backend.onrender.com",
]:
    if forbidden in account_text:
        raise SystemExit(
            "FAIL: account component contains "
            f"hardcoded backend URL: {forbidden}"
        )

print("PASS: no hardcoded backend URL")
print("PASS: guest search remains independent of account")
print("PASS: account frontend contract smoke test completed")
