#!/usr/bin/env python3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "render_setup": REPO_ROOT / "docs" / "RENDER_BACKEND_SETUP.md",
    "render_readiness": REPO_ROOT / "scripts" / "render_backend_readiness.sh",
    "render_yaml": REPO_ROOT / "render.yaml",
    "requirements": REPO_ROOT / "app" / "requirements.txt",
}

def main():
    print("RailYatra Render backend readiness smoke test")
    print("Mode: static Render deployment preparation check")

    for name, path in FILES.items():
        found = "yes" if path.exists() else "missing"
        print(f"{name} exists: {found}")
        if not path.exists():
            print(f"FAIL: missing {path.relative_to(REPO_ROOT)}")
            return 1

    combined = ""
    for path in FILES.values():
        combined += path.read_text(encoding="utf-8") + "\n"

    required = [
        "Root Directory: app",
        "Build Command: pip install -r requirements.txt",
        "Start Command: uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT",
        "RAILYATRA_ALLOWED_ORIGINS",
        "RAILYATRA_LIVE_BOOKING_ENABLED=false",
        "RAILYATRA_PAYMENT_ENABLED=false",
        "Real railway route recommendation preview",
        "RENDER BACKEND READINESS RESULT: PASS",
    ]

    missing_items = []
    for phrase in required:
        found = "yes" if phrase in combined else "missing"
        print(f"phrase {phrase}: {found}")
        if phrase not in combined:
            missing_items.append(phrase)

    if missing_items:
        print("FAIL: Render backend readiness missing phrase(s)")
        for item in missing_items:
            print(f"  missing: {item}")
        return 1

    print("Render backend setup docs present: yes")
    print("Render backend readiness script present: yes")
    print("PASS: Render backend readiness smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
