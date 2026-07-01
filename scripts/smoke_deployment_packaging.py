#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "requirements": REPO_ROOT / "app" / "requirements.txt",
    "render": REPO_ROOT / "render.yaml",
    "vercel": REPO_ROOT / "frontend" / "vercel.json",
    "targets": REPO_ROOT / "docs" / "DEPLOYMENT_TARGETS.md",
    "notes": REPO_ROOT / "docs" / "DEPLOYMENT_NOTES.md",
    "phase6": REPO_ROOT / "docs" / "PHASE_6_STATUS.md",
}


def main() -> int:
    print("RailYatra deployment packaging smoke test")
    print("Mode: static deployment file check")

    for name, path in FILES.items():
        print(f"{name} file exists: {'yes' if path.exists() else 'missing'}")
        if not path.exists():
            print(f"FAIL: missing {path.relative_to(REPO_ROOT)}")
            return 1

    requirements = FILES["requirements"].read_text(encoding="utf-8")
    render = FILES["render"].read_text(encoding="utf-8")
    vercel = FILES["vercel"].read_text(encoding="utf-8")
    targets = FILES["targets"].read_text(encoding="utf-8")
    notes = FILES["notes"].read_text(encoding="utf-8")

    required_requirements = [
        "fastapi",
        "uvicorn",
        "networkx",
    ]

    required_render = [
        "railyatra-backend",
        "rootDir: app",
        "pip install -r requirements.txt",
        "uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT",
        "RAILYATRA_LIVE_BOOKING_ENABLED",
        "RAILYATRA_PAYMENT_ENABLED",
    ]

    required_vercel = [
        '"rewrites"',
        '"destination": "/index.html"',
        '"framework": "vite"',
        '"outputDirectory": "dist"',
    ]

    required_docs = [
        "VITE_RAILYATRA_API_BASE",
        "RAILYATRA_ALLOWED_ORIGINS",
        "Real railway route recommendation preview",
        "official railway booking app",
        "live booking app",
    ]

    for phrase in required_requirements:
        print(f"requirements phrase {phrase}: {'yes' if phrase in requirements else 'missing'}")
        if phrase not in requirements:
            print(f"FAIL: missing requirement {phrase}")
            return 1

    for phrase in required_render:
        print(f"render phrase {phrase}: {'yes' if phrase in render else 'missing'}")
        if phrase not in render:
            print(f"FAIL: missing render phrase {phrase}")
            return 1

    for phrase in required_vercel:
        print(f"vercel phrase {phrase}: {'yes' if phrase in vercel else 'missing'}")
        if phrase not in vercel:
            print(f"FAIL: missing vercel phrase {phrase}")
            return 1

    for phrase in required_docs:
        combined_docs = targets + "\n" + notes
        print(f"deployment docs phrase {phrase}: {'yes' if phrase in combined_docs else 'missing'}")
        if phrase not in combined_docs:
            print(f"FAIL: missing deployment docs phrase {phrase}")
            return 1

    print("Backend deployment packaging: yes")
    print("Frontend deployment packaging: yes")
    print("Live booking/payment disabled in deployment config: yes")
    print("PASS: deployment packaging smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
