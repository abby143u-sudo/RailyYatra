#!/usr/bin/env python3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "readme": REPO_ROOT / "README.md",
    "demo_script": REPO_ROOT / "docs" / "PUBLIC_DEMO_SCRIPT.md",
    "launch_checklist": REPO_ROOT / "docs" / "LAUNCH_CHECKLIST.md",
    "deployment_notes": REPO_ROOT / "docs" / "DEPLOYMENT_NOTES.md",
    "phase6": REPO_ROOT / "docs" / "PHASE_6_STATUS.md",
}

def check_phrases(name, text, phrases):
    missing_items = []
    for phrase in phrases:
        found = "yes" if phrase in text else "missing"
        print(f"{name} phrase {phrase}: {found}")
        if phrase not in text:
            missing_items.append(phrase)
    return missing_items

def main():
    print("RailYatra public demo docs smoke test")
    print("Mode: static documentation safety check")

    for name, path in FILES.items():
        found = "yes" if path.exists() else "missing"
        print(f"{name} exists: {found}")
        if not path.exists():
            print(f"FAIL: missing {path.relative_to(REPO_ROOT)}")
            return 1

    readme = FILES["readme"].read_text(encoding="utf-8")
    demo = FILES["demo_script"].read_text(encoding="utf-8")
    launch = FILES["launch_checklist"].read_text(encoding="utf-8")
    notes = FILES["deployment_notes"].read_text(encoding="utf-8")
    phase6 = FILES["phase6"].read_text(encoding="utf-8")

    missing_items = []
    missing_items.extend(check_phrases("README", readme, [
        "Real railway route recommendation preview",
        "Local quickstart",
        "scripts/check_all.sh",
        "scripts/pre_import_gate.sh",
        "VITE_RAILYATRA_API_BASE",
        "RAILYATRA_ALLOWED_ORIGINS",
        "RAILYATRA_LIVE_BOOKING_ENABLED=false",
    ]))
    missing_items.extend(check_phrases("PUBLIC_DEMO_SCRIPT", demo, [
        "RailYatra is a real railway route recommendation preview.",
        "Do not say",
        "live booking app",
        "Sample route for demo",
        "This is a railway route recommendation preview, not a live ticket booking service yet.",
    ]))
    missing_items.extend(check_phrases("LAUNCH_CHECKLIST", launch, [
        "Before local demo",
        "Before backend deploy",
        "Before frontend deploy",
        "After backend deploy",
        "After frontend deploy",
        "Must not claim",
        "Ready-to-share only when",
    ]))
    missing_items.extend(check_phrases("DEPLOYMENT_NOTES", notes, [
        "Public demo documents",
        "Real railway route recommendation preview",
    ]))
    missing_items.extend(check_phrases("PHASE_6_STATUS", phase6, [
        "README quickstart",
        "public demo script",
        "launch checklist",
    ]))

    if missing_items:
        print("FAIL: public demo documentation missing required phrase(s)")
        for phrase in missing_items:
            print(f"  missing: {phrase}")
        return 1

    print("README quickstart present: yes")
    print("Public demo script present: yes")
    print("Launch checklist present: yes")
    print("Live booking false-claim guard present: yes")
    print("PASS: public demo docs smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
