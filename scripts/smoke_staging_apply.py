#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_dry_run() -> int:
    script = REPO_ROOT / "scripts" / "apply_staging_import.py"

    if not script.exists():
        print(f"FAIL: staging apply skeleton not found: {script}")
        return 1

    result = subprocess.run(
        [sys.executable, str(script), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    print(result.stdout, end="")

    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if result.returncode != 0:
        print("FAIL: staging apply skeleton dry-run failed")
        return result.returncode

    required_phrases = [
        "RailYatra staging apply skeleton",
        "Mode: dry-run",
        "Database opened: no",
        "Database write skipped: yes",
        "Railway production tables modified: no",
        "Apply mode status: disabled placeholder",
        "PASS: staging apply skeleton dry-run completed",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in result.stdout]

    if missing:
        print("FAIL: staging apply skeleton output missing expected phrase(s)")
        for phrase in missing:
            print(f"  missing: {phrase}")
        return 1

    return 0


def run_apply_placeholder_check() -> int:
    script = REPO_ROOT / "scripts" / "apply_staging_import.py"

    result = subprocess.run(
        [sys.executable, str(script), "--apply"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    print(result.stdout, end="")

    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if result.returncode == 0:
        print("FAIL: apply placeholder should not succeed yet")
        return 1

    required_phrases = [
        "Mode: apply",
        "APPLY IS NOT ENABLED YET",
        "Database opened: no",
        "Database write skipped: yes",
        "FAIL: apply mode placeholder is disabled by design",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in result.stdout]

    if missing:
        print("FAIL: apply placeholder output missing expected phrase(s)")
        for phrase in missing:
            print(f"  missing: {phrase}")
        return 1

    print("PASS: apply placeholder is safely blocked")
    return 0


def main() -> int:
    dry_run_code = run_dry_run()

    if dry_run_code != 0:
        return dry_run_code

    apply_code = run_apply_placeholder_check()

    if apply_code != 0:
        return apply_code

    print("PASS: staging apply skeleton smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
