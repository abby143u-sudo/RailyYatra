from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

checks = {
    ROOT / "frontend/src/components/AccountRecoveryDialog.jsx": [
        "/auth/forgot-password",
        "/auth/reset-password",
        "/auth/email-verification/confirm",
        "verificationRequestCache",
    ],
    ROOT / "frontend/src/components/AccountRecoveryDialog.css": [
        ".account-recovery-dialog",
        ".account-recovery-dialog__status.is-success",
    ],
    ROOT / "frontend/src/components/UserAccountPanel.jsx": [
        "AccountRecoveryDialog",
        "/auth/email-verification/resend",
        'mode: "forgot"',
        'mode: "verify"',
        'mode: "reset"',
    ],
    ROOT / "frontend/src/components/UserAccountPanel.css": [
        ".user-account-panel__verification",
    ],
}

missing: list[str] = []

for path, markers in checks.items():
    if not path.exists():
        missing.append(f"missing file: {path.relative_to(ROOT)}")
        continue

    content = path.read_text(encoding="utf-8")

    for marker in markers:
        if marker not in content:
            missing.append(
                f"{path.relative_to(ROOT)} missing marker: {marker}"
            )

if missing:
    raise SystemExit(
        "Phase 37 frontend recovery smoke failed:\n- "
        + "\n- ".join(missing)
    )

print("Phase 37 frontend recovery smoke: OK")
