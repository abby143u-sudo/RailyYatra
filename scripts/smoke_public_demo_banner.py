#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PATH = REPO_ROOT / "frontend" / "src" / "components" / "PublicDemoWarningBanner.jsx"
APP_PATH = REPO_ROOT / "frontend" / "src" / "App.jsx"
CSS_PATH = REPO_ROOT / "frontend" / "src" / "App.css"


def main() -> int:
    print("RailYatra public demo banner smoke test")
    print("Mode: static frontend safety copy check")

    for path in [COMPONENT_PATH, APP_PATH, CSS_PATH]:
        if not path.exists():
            print(f"FAIL: missing {path.relative_to(REPO_ROOT)}")
            return 1

    component = COMPONENT_PATH.read_text(encoding="utf-8")
    app = APP_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")

    required_component_phrases = [
        "Public beta preview",
        "real railway route recommendation preview",
        "Live booking",
        "Not connected",
        "Live ticket booking, PNR, payment, cancellation, live fare and live seat availability are not connected yet.",
        "route discovery",
        "ranked recommendations",
        "transfer safety",
    ]

    required_app_phrases = [
        'import PublicDemoWarningBanner from "./components/PublicDemoWarningBanner.jsx";',
        "<PublicDemoWarningBanner />",
    ]

    required_css_phrases = [
        "public-demo-warning-banner",
        "Public demo warning banner start",
        "Public demo warning banner end",
    ]

    missing_component = [phrase for phrase in required_component_phrases if phrase not in component]
    missing_app = [phrase for phrase in required_app_phrases if phrase not in app]
    missing_css = [phrase for phrase in required_css_phrases if phrase not in css]

    print("Public demo banner component checks:")
    for phrase in required_component_phrases:
        print(f"  {phrase}: {'yes' if phrase in component else 'missing'}")

    print("Public demo banner App.jsx checks:")
    for phrase in required_app_phrases:
        print(f"  {phrase}: {'yes' if phrase in app else 'missing'}")

    print("Public demo banner CSS checks:")
    for phrase in required_css_phrases:
        print(f"  {phrase}: {'yes' if phrase in css else 'missing'}")

    if missing_component:
        print("FAIL: public demo banner missing safety copy")
        for phrase in missing_component:
            print(f"  missing: {phrase}")
        return 1

    if missing_app:
        print("FAIL: App.jsx missing public demo banner wiring")
        for phrase in missing_app:
            print(f"  missing: {phrase}")
        return 1

    if missing_css:
        print("FAIL: App.css missing public demo banner styles")
        for phrase in missing_css:
            print(f"  missing: {phrase}")
        return 1

    print("Public beta label visible: yes")
    print("Live booking warning visible: yes")
    print("Payment/PNR/fare/availability warning visible: yes")
    print("PASS: public demo banner smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
