# RailYatra Stabilization Checkpoint

Checkpoint date: 30 June 2026

## Repository status

The stabilization baseline is clean. The combined check now validates the API, migration safety, read-only ingestion workflow, dry-run import CLI, and frontend build:

- Backend smoke test: 4 passed, 0 skipped
- Migration safety check: passed in in-memory SQLite
- Ingestion smoke test: passed
- Dry-run railway data import: passed with database writes skipped
- Frontend production build: passed
- Generated `frontend/dist/`: removed after validation

The active backend entry point remains `app/backend/api/main.py`. The inactive legacy backend at `archive_legacy/api.py` must not be edited.

## Latest commits

Recent stabilization work on `main`:

| Commit | Change |
| --- | --- |
| `c3ddaf6` | Include migration smoke in combined check |
| `86731f4` | Add non-destructive migration scaffold |
| `e8f3626` | Include ingestion checks in combined smoke test |
| `b285f81` | Add dry-run railway data import CLI |
| `8ab9323` | Add dry-run railway data ingestion scaffold |
| `792ec97` | Use deterministic database path |
| `5e141b6` | Add project gitignore rules |
| `48c8c51` | Add combined smoke check |
| `98ff637` | Add project run and test instructions |
| `bcaa193` | Add frontend smoke test |
| `d8c17aa` | Add backend smoke test |
| `88c5bb0` | Add project status documentation |

## Smoke test commands

Run all checks from the repository root:

```bash
./scripts/check_all.sh
```

Run the checks separately when diagnosing a failure:

```bash
python3 scripts/smoke_backend.py
python3 scripts/smoke_migrations.py
python3 scripts/smoke_ingestion.py
python3 scripts/import_railway_data.py --dry-run
python3 scripts/import_railway_data.py --dry-run --report-json
scripts/smoke_frontend.sh
```

The ingestion implementation is `app/backend/ingestion/railway_data.py`. It reads the existing raw JSON files and reports counts and missing fields without opening SQLite. Migration files live in `app/backend/database/migrations/`, and `001_ingestion_metadata.sql` is validated only against in-memory SQLite by `scripts/smoke_migrations.py`. The backend smoke test requires FastAPI `TestClient` dependencies, including `httpx`, in the active Python environment. The frontend smoke test builds the application and removes `frontend/dist/` afterward.

## Migration safety workflow

The current migration scaffold creates only `ingestion_runs`, `ingestion_source_files`, and `ingestion_issues` with `CREATE TABLE IF NOT EXISTS`. It has not been applied to `app/railyatra.db`.

- Migrations must remain non-destructive unless a destructive change is explicitly approved.
- Never alter `stations`, `trains`, `train_stops`, or `official_fares` without a database backup and reviewed dry-run report.
- Treat `archive_legacy/` as historical reference only; do not edit it.
- Run `python3 scripts/smoke_migrations.py` and `scripts/check_all.sh` before considering any apply step.

## Current railway data gaps

- Current SQLite train rows lack source and destination values, although the raw train JSON provides them.
- Station state coverage is incomplete in raw JSON and absent from current SQLite station rows.
- Some raw station records lack coordinates.
- The `schedules` and legacy `fares` tables are empty.
- Only limited manually verified fare data is available.
- Running-day data is unavailable in the current train schema.

The ingestion scaffold and CLI are read-only. They must not write to `app/railyatra.db` yet.

## Development run commands

Start the backend from the repository root:

```bash
cd app
uvicorn backend.api.main:app --reload
```

Start the frontend in a separate terminal:

```bash
cd frontend
npm run dev
```

The backend defaults to `http://127.0.0.1:8000`; health information is available from `GET /health`.

## Next phase: backend data ingestion and real railway data

The dry-run inspection and non-destructive migration scaffolds are complete. The next development phase should add an explicitly approved migration apply workflow and an idempotent, transactional importer before adding more route-search UI features.

1. Define the target data model for stations, trains, stops, service calendars, route timings, classes, and fares. Document required fields, identifiers, relationships, and update frequency.
2. Evaluate railway data sources for accuracy, coverage, update cadence, licensing, terms of use, and redistribution constraints. Keep source selection explicit; do not treat scraped or unofficial data as authoritative without provenance.
3. Introduce a raw staging area that preserves source files unchanged. Record source name, retrieval time, checksum, schema version, and import status for every dataset.
4. Build source-specific adapters that normalize data into one canonical schema. Keep parsing and validation separate from database writes so malformed rows can be reported safely.
5. Make imports idempotent and transactional. Re-running the same input should not create duplicates or leave partially imported data.
6. Add validation for station codes, train numbers, stop ordering, arrival/departure formats, day offsets, impossible timings, missing references, and duplicate services.
7. Publish ingestion summaries with accepted, rejected, inserted, updated, and unchanged counts. Preserve row-level error details for investigation.
8. Add fixture-based ingestion tests before importing large datasets. Extend smoke checks to verify database counts and one known route only after stable fixtures are available.
9. Define incremental refresh and rollback procedures. Keep the last known-good dataset available when a new import fails validation.
10. Track freshness and provenance in API responses where useful, especially for schedules and fares. Present estimates and official values distinctly.

The next implementation milestone should be an idempotent transactional importer that records an ingestion run and source-file metadata first, then imports normalized railway data only after dry-run approval. It must support deterministic re-runs and safe rollback.

## Safety rules for the next phase

- Keep imports out of request handlers; use dedicated scripts or services.
- Back up the local database before schema migrations or large imports.
- Keep the current ingestion workflow read-only until the migration and transactional import design are reviewed.
- Keep migrations non-destructive unless a destructive change is explicitly approved.
- Never change core railway or verified-fare tables without a backup and reviewed dry-run report.
- Never commit local databases, raw restricted datasets, credentials, `frontend/dist/`, or backup files.
- Review `git status --short` and run `./scripts/check_all.sh` before each commit.
- Continue to leave all of `archive_legacy/` untouched.

## Backup and Migration Checkpoint

Current safe workflow:

    python3 scripts/backup_database.py
    python3 scripts/run_migrations.py --dry-run
    python3 scripts/run_migrations.py --apply
    scripts/check_all.sh

Safety checkpoint:

- Backup utility exists.
- Safe migration runner exists.
- Combined smoke check includes migration dry-run.
- Frontend build remains clean.
- Backend smoke remains clean.
- Ingestion dry-run remains read-only.
- app/railyatra.db should not be manually edited.
- archive_legacy/ should not be edited.

Next phase:

Build an idempotent transactional importer that writes ingestion metadata first, validates raw JSON, then imports normalized railway data only after dry-run approval.

## Metadata Writer Checkpoint

Metadata-only ingestion writer status:

- Dry-run supported.
- Apply mode supported.
- Backup is created before apply.
- Railway data tables are not modified.
- Smoke test exists.
- Combined check includes metadata writer smoke test.

Next safe step:

Use metadata writer output to design the first idempotent transactional importer, but do not write normalized railway data until dry-run reports are approved.

## Verifier Checkpoint

Ingestion metadata verifier status:

- Dry-run supported.
- Dry-run included in combined check.
- Live metadata verification supported after metadata apply.
- Verifier checks metadata schema and latest ingestion audit state.
- Railway train, station, route, stop, and fare data remains protected.

Next safe step:

Build a strict pre-import gate that blocks real railway data writes unless migrations, smoke tests, dry-run import, metadata writer, and verifier all pass.

## Pre-Import Gate Checkpoint

Pre-import safety gate status:

- Backend smoke test included.
- Migration smoke test included.
- Migration runner dry-run included.
- Raw railway ingestion inspection included.
- Railway data import dry-run included.
- Metadata writer smoke test included.
- Ingestion metadata verifier dry-run included.
- Frontend production build included.
- Real railway data writes blocked until manual review.

Next safe step:

Create a real import design document before writing normalized railway data into production tables.

## Staging Planner Checkpoint

Staging planner status:

- Dry-run planner exists.
- Smoke test exists.
- Combined check includes planner smoke test.
- Pre-import gate includes planner smoke test.
- No database writes happen in planner dry-run.
- No railway production tables are modified.

Next safe step:

Design staging apply mode, but keep it disabled until backup, transaction, validation, and rollback rules are implemented.

## Staging Apply Skeleton Checkpoint

Staging apply skeleton status:

- Safe skeleton exists.
- Smoke test exists.
- Combined check includes skeleton smoke test.
- Pre-import gate includes skeleton smoke test.
- Dry-run mode is safe and read-only.
- Apply mode is intentionally blocked.
- No real staging writes happen yet.

Next safe step:

Implement staging apply mode behind an explicit flag only after adding backup, transaction, staging-only delete rules, row inserts, validation, and rollback handling.
