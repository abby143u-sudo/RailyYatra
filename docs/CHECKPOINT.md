# RailYatra Stabilization Checkpoint

Checkpoint date: 30 June 2026

## Repository status

The stabilization baseline is clean. The combined check now validates the API, read-only ingestion workflow, dry-run import CLI, and frontend build:

- Backend smoke test: 4 passed, 0 skipped
- Ingestion smoke test: passed
- Dry-run railway data import: passed with database writes skipped
- Frontend production build: passed
- Generated `frontend/dist/`: removed after validation

The active backend entry point remains `app/backend/api/main.py`. The inactive legacy backend at `archive_legacy/api.py` must not be edited.

## Latest commits

Recent stabilization work on `main`:

| Commit | Change |
| --- | --- |
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
python3 scripts/smoke_ingestion.py
python3 scripts/import_railway_data.py --dry-run
python3 scripts/import_railway_data.py --dry-run --report-json
scripts/smoke_frontend.sh
```

The ingestion implementation is `app/backend/ingestion/railway_data.py`. It reads the existing raw JSON files and reports counts and missing fields without opening SQLite. The backend smoke test requires FastAPI `TestClient` dependencies, including `httpx`, in the active Python environment. The frontend smoke test builds the application and removes `frontend/dist/` afterward.

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

The dry-run inspection foundation is complete. The next development phase should introduce a non-destructive migration and an idempotent, transactional importer before adding more route-search UI features.

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

The next implementation milestone should be a documented ingestion contract, a small licensed fixture dataset, and a non-destructive migration that supports repeated transactional imports with deterministic results and safe rollback.

## Safety rules for the next phase

- Keep imports out of request handlers; use dedicated scripts or services.
- Back up the local database before schema migrations or large imports.
- Keep the current ingestion workflow read-only until the migration and transactional import design are reviewed.
- Never commit local databases, raw restricted datasets, credentials, `frontend/dist/`, or backup files.
- Review `git status --short` and run `./scripts/check_all.sh` before each commit.
- Continue to leave `archive_legacy/api.py` untouched.
