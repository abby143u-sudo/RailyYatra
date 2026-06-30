#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    script = REPO_ROOT / "scripts" / "verify_staging_import.py"

    if not script.exists():
        print(f"FAIL: staging verifier not found: {script}")
        return 1

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    print(result.stdout, end="")

    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if result.returncode != 0:
        print("FAIL: staging verifier failed")
        return result.returncode

    required_phrases = [
        "RailYatra staging import verifier",
        "staging_stations:",
        "staging_trains:",
        "staging_train_stops:",
        "Production railway tables modified: no",
        "PASS: staging import verified",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in result.stdout]

    if missing:
        print("FAIL: staging verifier output missing expected phrase(s)")
        for phrase in missing:
            print(f"  missing: {phrase}")
        return 1

    print("PASS: staging verifier smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
