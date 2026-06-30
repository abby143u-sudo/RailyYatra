# RailYatra Staging Apply Mode Design

## Purpose

This document defines how RailYatra will safely write raw railway data into staging tables.

This design does not enable production railway table writes.

## Current Safety Foundation

Already implemented:

- Raw data inspection
- Railway import dry-run
- Metadata-only ingestion writer
- Metadata verifier true dry-run
- Multi-migration smoke test
- Safe migration runner
- Pre-import safety gate
- Staging import dry-run planner
- Staging table migration

Current staging tables:

- staging_stations
- staging_trains
- staging_train_stops

## Important Rule

Staging apply mode may write only to staging tables.

Allowed tables:

- staging_stations
- staging_trains
- staging_train_stops
- ingestion_runs
- ingestion_source_files
- ingestion_issues

Forbidden tables:

- production station tables
- production train tables
- production train stop tables
- route/search graph tables
- fare tables
- user-facing journey result tables

## Proposed Command

Future command:

    python3 scripts/apply_staging_import.py --apply

Dry-run command:

    python3 scripts/apply_staging_import.py --dry-run

Default command without flags should behave as dry-run.

## Required Pre-Apply Gate

Before any staging write, apply script must run:

    scripts/pre_import_gate.sh

If the gate fails, staging apply must stop.

## Required Backup

Before any staging write, apply script must run:

    python3 scripts/backup_database.py

If backup fails, staging apply must stop.

## Transaction Rules

Staging apply must use one database transaction:

1. open database
2. enable foreign keys
3. start transaction
4. create ingestion run row
5. clear only staging rows for current staging run strategy
6. insert staging stations
7. insert staging trains
8. insert staging train stops
9. validate staging counts
10. validate required keys
11. validate orphan train numbers
12. validate orphan station codes
13. commit only if all validations pass
14. rollback on any error

## Delete Rules

Staging apply may clear staging tables only.

Allowed:

    DELETE FROM staging_stations
    DELETE FROM staging_trains
    DELETE FROM staging_train_stops

Not allowed:

    DELETE FROM stations
    DELETE FROM trains
    DELETE FROM train_stops
    DELETE FROM fares
    DELETE FROM any production table

## Validation Rules

Blocking validations:

- station code missing
- train number missing
- schedule train number missing
- schedule station code missing
- orphan schedule train number
- orphan schedule station code
- unexpectedly low row counts
- staging insert count mismatch

Non-blocking warnings:

- station name missing
- train name missing
- station state missing
- station coordinates missing
- schedule arrival missing
- schedule departure missing

## Expected Row Counts

Based on latest dry-run data:

- staging_stations: 8990
- staging_trains: 5208
- staging_train_stops: 417080

Apply mode should fail if row counts are unexpectedly low.

## Post-Apply Checks

After successful staging apply:

    python3 scripts/verify_ingestion_metadata.py
    python3 scripts/smoke_backend.py
    scripts/check_all.sh

Production behavior should remain unchanged because production tables are untouched.

## Rollback Test

Before trusting staging apply:

1. create backup
2. run apply on staging
3. verify staging counts
4. restore backup manually in test
5. confirm project still passes checks

## Next Implementation Step

Create safe skeleton script:

    scripts/apply_staging_import.py

First version must support:

- --dry-run
- --apply flag placeholder
- pre-import gate check
- backup check
- no production writes
- clear safety print statements

Actual staging row inserts should come after skeleton review.

## Skeleton Implemented

Safe skeleton implemented:

    scripts/apply_staging_import.py

Smoke test implemented:

    scripts/smoke_staging_apply.py

Current skeleton behavior:

- --dry-run is safe and read-only.
- --apply is blocked by design.
- Production railway tables are not touched.
- Staging rows are not written yet.

Next implementation requirement:

Before enabling --apply, the script must run pre-import gate, create a backup, open a transaction, write only staging tables, validate counts, validate orphan references, and rollback on failure.

## Staging Verification Implemented

Staging verification is implemented.

Commands:

    python3 scripts/verify_staging_import.py
    python3 scripts/smoke_staging_verifier.py

The verifier checks:

- staging_stations count
- staging_trains count
- staging_train_stops count
- production railway tables modified: no

This completes the Phase 2.5 staging safety loop.
