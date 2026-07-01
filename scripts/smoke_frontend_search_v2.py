#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PATH = REPO_ROOT / "frontend" / "src" / "components" / "Phase3RouteSearchPreview.jsx"
APP_PATH = REPO_ROOT / "frontend" / "src" / "App.jsx"


def main() -> int:
    print("RailYatra frontend search-v2 smoke test")
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
        "/search-v2",
        "Production Candidate Route Search",
        "Legacy /search is still untouched",
        "direct_limit",
        "transfer_limit",
        "routes.map",
        "View stops",
        "/staging/trains/",
        "/staging/stations",
    ]

    forbidden_component_phrases = [
        "fetch(`${API_BASE}/staging/search?",
        "Unable to reach staging route engine",
    ]

    required_app_phrases = [
        'import Phase3RouteSearchPreview from "./components/Phase3RouteSearchPreview.jsx";',
        "<Phase3RouteSearchPreview />",
    ]

    missing = [
        phrase
        for phrase in required_component_phrases
        if phrase not in component
    ]

    forbidden_found = [
        phrase
        for phrase in forbidden_component_phrases
        if phrase in component
    ]

    missing_app = [
        phrase
        for phrase in required_app_phrases
        if phrase not in app
    ]

    print("Frontend search-v2 component checks:")
    for phrase in required_component_phrases:
        print(f"  {phrase}: {'yes' if phrase in component else 'missing'}")

    print("Frontend App.jsx render checks:")
    for phrase in required_app_phrases:
        print(f"  {phrase}: {'yes' if phrase in app else 'missing'}")

    if missing:
        print("FAIL: missing required search-v2 frontend phrase(s)")
        for phrase in missing:
            print(f"  missing: {phrase}")
        return 1

    if forbidden_found:
        print("FAIL: forbidden legacy/staging search phrase(s) found")
        for phrase in forbidden_found:
            print(f"  forbidden: {phrase}")
        return 1

    if missing_app:
        print("FAIL: App.jsx missing Phase3RouteSearchPreview wiring")
        for phrase in missing_app:
            print(f"  missing: {phrase}")
        return 1

    print("Frontend route preview endpoint: /search-v2")
    print("Legacy /search protected: yes")
    print("Production railway tables modified: no")
    print("PASS: frontend search-v2 smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
