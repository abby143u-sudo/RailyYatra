#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "app" / "railyatra.db"

PLAN_SCRIPT = REPO_ROOT / "scripts" / "plan_staging_import.py"
PRE_IMPORT_GATE = REPO_ROOT / "scripts" / "pre_import_gate.sh"
BACKUP_SCRIPT = REPO_ROOT / "scripts" / "backup_database.py"

ALLOWED_STAGING_TABLES = [
    "staging_stations",
    "staging_trains",
    "staging_train_stops",
]

ALLOWED_METADATA_TABLES = [
    "ingestion_runs",
    "ingestion_source_files",
    "ingestion_issues",
]

FORBIDDEN_PRODUCTION_TABLE_GROUPS = [
    "stations production tables",
    "trains production tables",
    "train stops production tables",
    "route/search graph tables",
    "fare tables",
    "user-facing journey result tables",
]


def run_command(label: str, command: list[str]) -> int:
    print("")
    print("========================================")
    print(f"RUNNING: {label}")
    print("========================================")

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
    )

    if result.returncode != 0:
        print(f"FAIL: {label}")
        return result.returncode

    print(f"PASS: {label}")
    return 0


def verify_required_files() -> int:
    required_files = [
        PLAN_SCRIPT,
        PRE_IMPORT_GATE,
        BACKUP_SCRIPT,
        DB_PATH,
    ]

    missing = [path for path in required_files if not path.exists()]

    if missing:
        print("FAIL: required file(s) missing")
        for path in missing:
            print(f"  missing: {path}")
        return 1

    return 0


def print_safety_scope() -> None:
    print("Allowed staging tables:")
    for table in ALLOWED_STAGING_TABLES:
        print(f"  {table}")

    print("Allowed metadata tables:")
    for table in ALLOWED_METADATA_TABLES:
        print(f"  {table}")

    print("Forbidden production table groups:")
    for item in FORBIDDEN_PRODUCTION_TABLE_GROUPS:
        print(f"  {item}")


def dry_run() -> int:
    print("RailYatra staging apply skeleton")
    print("Mode: dry-run")
    print(f"Database: {DB_PATH}")
    print("Database opened: no")
    print("Database write skipped: yes")
    print("Railway production tables modified: no")

    file_check = verify_required_files()

    if file_check != 0:
        return file_check

    print_safety_scope()

    plan_code = run_command(
        "Staging import planner dry-run",
        [sys.executable, str(PLAN_SCRIPT), "--dry-run"],
    )

    if plan_code != 0:
        return plan_code

    print("")
    print("Apply mode status: disabled placeholder")
    print("Next implementation must add backup + transaction + staging-only writes.")
    print("PASS: staging apply skeleton dry-run completed")
    return 0


def apply_placeholder() -> int:
    print("RailYatra staging apply skeleton")
    print("Mode: apply")
    print("APPLY IS NOT ENABLED YET")
    print("Database opened: no")
    print("Database write skipped: yes")
    print("Railway production tables modified: no")
    print("")
    print("Reason:")
    print("  Staging apply mode is intentionally blocked until the skeleton is reviewed.")
    print("")
    print("Required future apply sequence:")
    print("  1. run scripts/pre_import_gate.sh")
    print("  2. create database backup")
    print("  3. open transaction")
    print("  4. write only staging and ingestion metadata tables")
    print("  5. validate counts and orphan references")
    print("  6. commit only if all validations pass")
    print("")
    print("FAIL: apply mode placeholder is disabled by design")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safe skeleton for future staging railway import writes."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run staging apply planning without opening or writing the database.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Placeholder only. Apply mode is intentionally disabled for now.",
    )

    args = parser.parse_args()

    if args.dry_run and args.apply:
        print("FAIL: choose either --dry-run or --apply, not both")
        return 2

    if args.apply:
        return apply_placeholder()

    return dry_run()


if __name__ == "__main__":
    raise SystemExit(main())
