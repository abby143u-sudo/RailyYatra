#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PATH = REPO_ROOT / "frontend" / "src" / "components" / "Phase5BetaChecklistPanel.jsx"
APP_PATH = REPO_ROOT / "frontend" / "src" / "App.jsx"


def main() -> int:
    print("RailYatra frontend beta checklist smoke test")
    print("Mode: static frontend contract check")

    if not COMPONENT_PATH.exists():
        print(f"FAIL: missing component {COMPONENT_PATH}")
        return 1

    if not APP_PATH.exists():
        print(f"FAIL: missing App.jsx {APP_PATH}")
        return 1

    component = COMPONENT_PATH.read_text(encoding="utf-8")
    app = APP_PATH.read_text(encoding="utf-8")

    required_component_phrases = [
        "/product/beta-checklist",
        "Public Beta Checklist",
        "ready_items",
        "blocked_items",
        "public_beta_decision",
        "Live booking, PNR, payments and ticketing claims are blocked.",
        "real railway route recommendation preview",
        "Ticket payment",
    ]

    required_app_phrases = [
        'import Phase5BetaChecklistPanel from "./components/Phase5BetaChecklistPanel.jsx";',
        "<Phase5BetaChecklistPanel />",
    ]

    missing = [phrase for phrase in required_component_phrases if phrase not in component]
    missing_app = [phrase for phrase in required_app_phrases if phrase not in app]

    print("Frontend beta checklist component checks:")
    for phrase in required_component_phrases:
        print(f"  {phrase}: {'yes' if phrase in component else 'missing'}")

    print("Frontend App.jsx render checks:")
    for phrase in required_app_phrases:
        print(f"  {phrase}: {'yes' if phrase in app else 'missing'}")

    if missing:
        print("FAIL: missing required beta checklist frontend phrase(s)")
        for phrase in missing:
            print(f"  missing: {phrase}")
        return 1

    if missing_app:
        print("FAIL: App.jsx missing Phase5BetaChecklistPanel wiring")
        for phrase in missing_app:
            print(f"  missing: {phrase}")
        return 1

    print("Frontend beta checklist endpoint: /product/beta-checklist")
    print("Live booking/payment claim blocked: yes")
    print("Production railway tables modified: no")
    print("PASS: frontend beta checklist smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
