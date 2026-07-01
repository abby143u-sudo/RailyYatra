#!/usr/bin/env python3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "deploy_preflight": REPO_ROOT / "scripts" / "deploy_preflight.sh",
    "manual_steps": REPO_ROOT / "docs" / "PHASE_7_MANUAL_DEPLOYMENT_STEPS.md",
    "runbook": REPO_ROOT / "docs" / "PHASE_7_DEPLOYMENT_RUNBOOK.md",
    "deployed_smoke": REPO_ROOT / "scripts" / "smoke_deployed_public_demo.py",
}

def main():
    print("RailYatra Phase 7 deploy preflight docs smoke test")
    print("Mode: static deploy readiness check")

    for name, path in FILES.items():
        found = "yes" if path.exists() else "missing"
        print(f"{name} exists: {found}")
        if not path.exists():
            print(f"FAIL: missing {path.relative_to(REPO_ROOT)}")
            return 1

    preflight = FILES["deploy_preflight"].read_text(encoding="utf-8")
    manual = FILES["manual_steps"].read_text(encoding="utf-8")
    runbook = FILES["runbook"].read_text(encoding="utf-8")
    deployed_smoke = FILES["deployed_smoke"].read_text(encoding="utf-8")

    required = [
        "scripts/check_all.sh",
        "scripts/pre_import_gate.sh",
        "PHASE 7 DEPLOY PREFLIGHT RESULT: PASS",
        "git push -u origin main",
        "Render",
        "Vercel",
        "VITE_RAILYATRA_API_BASE",
        "RAILYATRA_ALLOWED_ORIGINS",
        "RAILYATRA_DEPLOYED_BACKEND_URL",
        "RAILYATRA_DEPLOYED_FRONTEND_URL",
        "Real railway route recommendation preview",
        "live ticket booking",
    ]

    combined = preflight + "\n" + manual + "\n" + runbook + "\n" + deployed_smoke
    missing_items = []

    for phrase in required:
        found = "yes" if phrase in combined else "missing"
        print(f"phrase {phrase}: {found}")
        if phrase not in combined:
            missing_items.append(phrase)

    if missing_items:
        print("FAIL: Phase 7 deploy docs missing phrase(s)")
        for item in missing_items:
            print(f"  missing: {item}")
        return 1

    print("Deploy preflight script present: yes")
    print("Manual deployment steps present: yes")
    print("Deployed smoke checker present: yes")
    print("PASS: Phase 7 deploy preflight docs smoke test completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
