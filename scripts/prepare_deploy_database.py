#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_IMPORTER = (
    REPO_ROOT
    / "app"
    / "scripts"
    / "prepare_deploy_database.py"
)


def main() -> int:
    if not FULL_IMPORTER.exists():
        print(
            "ERROR: Full deploy database importer not found:",
            FULL_IMPORTER,
            file=sys.stderr,
        )
        return 1

    print(
        "Delegating deploy database preparation to:",
        FULL_IMPORTER,
    )

    result = subprocess.run(
        [
            sys.executable,
            "-u",
            str(FULL_IMPORTER),
        ],
        cwd=REPO_ROOT,
        check=False,
    )

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
