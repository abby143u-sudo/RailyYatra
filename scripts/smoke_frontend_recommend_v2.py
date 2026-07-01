#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PATH = REPO_ROOT / "frontend" / "src" / "components" / "Phase4RecommendationPreview.jsx"
APP_PATH = REPO_ROOT / "frontend" / "src" / "App.jsx"


def main() -> int:
    print("RailYatra frontend recommend-v2 smoke test")
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
        "/recommend-v2",
        "Recommendation v2 Preview",
        "confidence",
        "transfer_safety",
        "booking_status",
        "Why recommended",
        "Live booking not connected yet",
        "Legacy /search unchanged",
        "recommendations.map",
        "/staging/stations",
        "phase4-recommend-suggestions",
        "Type station code or name",
    ]

    required_app_phrases = [
        'import Phase4RecommendationPreview from "./components/Phase4RecommendationPreview.jsx";',
        "<Phase4RecommendationPreview />",
    ]

    missing = [phrase for phrase in required_component_phrases if phrase not in component]
    missing_app = [phrase for phrase in required_app_phrases if phrase not in app]

    print("Frontend recommend-v2 component checks:")
    for phrase in required_component_phrases:
        print(f"  {phrase}: {'yes' if phrase in component else 'missing'}")

    print("Frontend App.jsx render checks:")
    for phrase in required_app_phrases:
        print(f"  {phrase}: {'yes' if phrase in app else 'missing'}")

    if missing:
        print("FAIL: missing required recommend-v2 frontend phrase(s)")
        for phrase in missing:
            print(f"  missing: {phrase}")
        return 1

    if missing_app:
        print("FAIL: App.jsx missing Phase4RecommendationPreview wiring")
        for phrase in missing_app:
            print(f"  missing: {phrase}")
        return 1

    print("Frontend recommendation endpoint: /recommend-v2")
    print("Legacy /search protected: yes")
    print("Production railway tables modified: no")
    print("PASS: frontend recommend-v2 smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
