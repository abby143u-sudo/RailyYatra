#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    script = REPO_ROOT / "scripts" / "write_ingestion_metadata.py"

    if not script.exists():
        print(f"FAIL: metadata writer not found: {script}")
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
        print("FAIL: metadata writer dry-run failed")
        return result.returncode

    required_phrases = [
        "Mode: dry-run",
        "Railway data tables modified: no",
        "Database write skipped: yes",
        "PASS: metadata write dry-run completed",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in result.stdout]

    if missing:
        print("FAIL: metadata writer output missing expected phrase(s)")
        for phrase in missing:
            print(f"  missing: {phrase}")
        return 1

    print("PASS: metadata writer smoke test completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
