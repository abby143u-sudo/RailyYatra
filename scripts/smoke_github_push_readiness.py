#!/usr/bin/env python3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "github_push_readiness": REPO_ROOT / "scripts" / "github_push_readiness.sh",
    "github_push_guide": REPO_ROOT / "docs" / "GITHUB_PUSH_GUIDE.md",
}

def main():
    print("RailYatra GitHub push readiness smoke test")
    print("Mode: static GitHub deployment preparation check")
    for name, path in FILES.items():
        found = "yes" if path.exists() else "missing"
        print(f"{name} exists: {found}")
        if not path.exists():
            print(f"FAIL: missing {path.relative_to(REPO_ROOT)}")
            return 1
    script = FILES["github_push_readiness"].read_text(encoding="utf-8")
    guide = FILES["github_push_guide"].read_text(encoding="utf-8")
    combined = script + "\n" + guide
    required = [
        "git remote add origin YOUR_GITHUB_REPO_URL",
        "git push -u origin main",
        "GITHUB PUSH READINESS RESULT: READY",
        "GITHUB PUSH READINESS RESULT: NEEDS_REMOTE",
        "Render",
        "Vercel",
        "Real railway route recommendation preview",
        "live booking",
        "payment",
        "PNR",
    ]
    missing_items = []
    for phrase in required:
        found = "yes" if phrase in combined else "missing"
        print(f"phrase {phrase}: {found}")
        if phrase not in combined:
            missing_items.append(phrase)
    if missing_items:
        print("FAIL: GitHub push readiness docs/script missing phrase(s)")
        for item in missing_items:
            print(f"  missing: {item}")
        return 1
    print("GitHub push readiness script present: yes")
    print("GitHub push guide present: yes")
    print("PASS: GitHub push readiness smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
