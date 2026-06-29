# RailYatra

RailYatra is a train alternate-route and smart journey recommendation app. It combines a FastAPI backend with a React/Vite frontend to search direct and transfer journeys, compare route options, apply journey filters, and surface booking and transfer guidance.

The active backend entry point is `app/backend/api/main.py`. The active frontend lives under `frontend/`.

## Run the backend

From the repository root:

```bash
cd app
uvicorn backend.api.main:app --reload
```

The API is available at `http://127.0.0.1:8000` by default.

## Run the frontend

In a separate terminal, from the repository root:

```bash
cd frontend
npm run dev
```

Vite prints the local frontend URL when the development server starts.

## Smoke tests

Run the backend smoke test from the repository root:

```bash
python3 scripts/smoke_backend.py
```

The backend smoke test uses FastAPI `TestClient` and checks `/`, `/health`, `/stations` when available, and `/search?source=PNBE&destination=NDLS`. Its Python environment must include the application requirements and `httpx`.

Run the frontend build smoke test from the repository root:

```bash
./scripts/smoke_frontend.sh
```

The frontend smoke test runs the production build, reports `PASS` or `FAIL`, removes `frontend/dist`, and returns a non-zero exit status when the build fails.

Run the complete project check:

```bash
scripts/check_all.sh
```

The combined check runs the backend smoke test, migration safety check, ingestion smoke test, dry-run railway data import, and frontend smoke test.

## Railway data ingestion (dry-run)

The read-only ingestion inspector is implemented in `app/backend/ingestion/railway_data.py`. It examines the existing station, train, and schedule JSON files without connecting to or writing to SQLite.

Print the dry-run report:

```bash
python3 scripts/import_railway_data.py --dry-run
```

Print the same report as JSON:

```bash
python3 scripts/import_railway_data.py --dry-run --report-json
```

Run the ingestion smoke test:

```bash
python3 scripts/smoke_ingestion.py
```

Current known data gaps:

- The current SQLite train records are missing source and destination values, although these fields exist in the raw train JSON.
- Station state coverage is incomplete in the raw data and absent from the current SQLite station records.
- Some stations are missing coordinates.
- The `schedules` and legacy `fares` tables are empty.
- Only a limited number of verified fares are available.
- Running-day data is unavailable in the current train schema.

The ingestion workflow is currently read-only and must not write to `app/railyatra.db`. The next phase is a non-destructive migration followed by an idempotent, transactional import process.

## Database migration safety

Migration files live in `app/backend/database/migrations/`. The current scaffold is `001_ingestion_metadata.sql`, which defines only ingestion metadata/support tables with `CREATE TABLE IF NOT EXISTS`.

Validate migration safety without opening the project database:

```bash
python3 scripts/smoke_migrations.py
```

The smoke test rejects destructive or data-writing statements and executes the migration only against in-memory SQLite. Migrations must remain non-destructive unless a destructive change is explicitly approved.

Never alter `stations`, `trains`, `train_stops`, or `official_fares` without first creating a database backup and reviewing a dry-run report. The next importer phase must be idempotent and transactional: it should write an ingestion run and source-file metadata first, then import normalized railway data only after dry-run approval.

## Health endpoint

With the backend running, open:

```text
http://127.0.0.1:8000/health
```

`GET /health` reports the backend health status and record counts for trains, stations, and train stops.

## Important project rules

- Treat all of `archive_legacy/` as historical reference only; do not edit it.
- Do not commit `frontend/dist/` or temporary backup files.
- Do not enable database writes in the current ingestion workflow.
- Keep migrations non-destructive unless a destructive operation is explicitly approved.
- Check `git status --short` before and after making changes.
- Run `scripts/check_all.sh` before committing.

## Database Backup and Migration Safety

Before any database write, create a SQLite backup:

    python3 scripts/backup_database.py

Check migration safety without touching the database:

    python3 scripts/run_migrations.py --dry-run

Apply approved non-destructive migrations only when explicitly needed:

    python3 scripts/run_migrations.py --apply

Run the full project check:

    scripts/check_all.sh

Safety rules:

- Backup before any database write.
- Migration default mode must stay dry-run.
- Actual migration apply must require explicit --apply.
- Never edit archive_legacy/.
- Never modify app/railyatra.db manually.
- Do not commit backups/.
- Do not commit frontend/dist.
- Do not alter existing railway tables such as stations, trains, train_stops, or official_fares without explicit approval, backup, and dry-run report.

Current migration status:

- Ingestion metadata migration scaffold exists.
- Existing train, station, route, and fare tables are protected.
- Future ingestion work should write metadata first, then import normalized railway data only after dry-run approval.

## Metadata-Only Ingestion Writer

RailYatra has a metadata-only ingestion writer for safe audit testing before real data imports.

Dry-run command:

    python3 scripts/write_ingestion_metadata.py --dry-run

Apply metadata-only audit write:

    python3 scripts/write_ingestion_metadata.py --apply

Smoke test command:

    python3 scripts/smoke_metadata_writer.py

Combined check:

    scripts/check_all.sh

Safety notes:

- Metadata writer must not modify railway data tables.
- It may only write audit rows to ingestion metadata tables.
- It must create a backup before apply mode.
- Default mode should remain dry-run.
- Real train, station, stop, and fare tables must stay untouched.
