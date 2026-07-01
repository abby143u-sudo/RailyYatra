# RailYatra Project Status

Last reviewed: 30 June 2026

## Current status

RailYatra is a FastAPI and React/Vite application for finding alternate train routes and generating smart journey recommendations. The active backend entry point is `app/backend/api/main.py`; the active frontend is primarily implemented in `frontend/src/App.jsx` and `frontend/src/App.css`.

The frontend production build and combined project checks currently pass. A read-only railway data ingestion inspector and dry-run CLI are available; neither writes to SQLite. Recent work has focused on stabilization, repeatable checks, deterministic database path resolution, and safe ingestion foundations.

The legacy backend at `archive_legacy/api.py` is inactive. Do not edit it.

## Backend route surface

The following routes were discovered in `app/backend/api/main.py`:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | API identity, status, and version |
| `GET` | `/health` | Health status and database record counts |
| `GET` | `/stations` | Station-code and station-name suggestions |
| `GET` | `/search` | Smart journey planning with date, class, train-type, and quota inputs |
| `GET` | `/direct` | Direct train routes between two stations |
| `GET` | `/transfer` | One-transfer routes between two stations |
| `GET` | `/train/{train_no}` | Train details and ordered stops |
| `GET` | `/station/{station_code}` | Station details and a sample of serving trains |
| `GET` | `/multi-route` | Multi-transfer route search |
| `GET` | `/fare` | Official fare-table lookup |
| `GET` | `/fares/stats` | Fare-table statistics |
| `GET` | `/fares` | Filtered fare records |
| `GET` | `/fares/import/files` | CSV files available for fare import |
| `POST` | `/fares/import` | Import fares from a CSV under `app/data/raw` |
| `GET` | `/fare/sources` | Available fare sources |
| `GET` | `/fare/lookup` | Best available fare lookup |
| `POST` | `/fare/manual` | Add or update a manually verified fare |

## Implemented frontend features

- Train-type, journey-date, quota, departure-time, maximum-fare, maximum-transfer-wait, and minimum-score filters
- Hide-unknown-fare toggle and reset-filters action
- Collapsible advanced filters and active filter chips
- Search form validation and station-code helper panel
- Favorite route saving with `localStorage`
- Route comparison shortlist and recent-search history
- WhatsApp-friendly share messages
- Journey confidence badge, smart warnings, transfer safety badge, and smart booking checklist
- Backend health status card connected to `/health`
- API error details panel
- Search summary statistics and best-route highlighting
- Polished route timeline details
- Route skeleton loader
- Empty-results suggestions and a clean no-results card

## Run commands

From the repository root:

```bash
cd ~/RailYatra 2>/dev/null || cd ~/railyatra
```

Start the backend:

```bash
cd app
uvicorn backend.api.main:app --reload
```

Start the frontend in a separate terminal:

```bash
cd frontend
npm run dev
```

## Build and test commands

Frontend production build:

```bash
cd ~/RailYatra 2>/dev/null || cd ~/railyatra
npm --prefix frontend run build
rm -rf frontend/dist
```

Frontend lint check:

```bash
cd ~/RailYatra 2>/dev/null || cd ~/railyatra
npm --prefix frontend run lint
```

Backend smoke test:

```bash
python3 scripts/smoke_backend.py
```

Ingestion smoke test and dry-run import:

```bash
python3 scripts/smoke_migrations.py
python3 scripts/smoke_ingestion.py
python3 scripts/import_railway_data.py --dry-run
python3 scripts/import_railway_data.py --dry-run --report-json
```

Combined project check:

```bash
scripts/check_all.sh
```

The combined check covers the backend API, migration safety, railway data inspection, dry-run import CLI, and frontend production build. It removes `frontend/dist/` after validation.

## Railway data ingestion status

The dry-run inspector lives at `app/backend/ingestion/railway_data.py`. It reads `app/data/raw/stations.json`, `trains.json`, and `schedules.json`, then reports record counts and missing-field totals. The CLI and smoke test are `scripts/import_railway_data.py` and `scripts/smoke_ingestion.py`.

Current known data gaps:

- The current SQLite train records are missing source and destination values; the raw train JSON contains those fields.
- Raw station state coverage is incomplete, and current SQLite station rows do not contain state values.
- Some raw stations have no usable coordinates.
- The `schedules` and legacy `fares` tables are empty.
- Only limited manually verified fare data exists.
- Running-day data is unavailable in the current train schema.

This ingestion version is strictly read-only. It must not create tables, migrate schemas, or write to `app/railyatra.db`. The next phase is a non-destructive migration plus an idempotent, transactional importer with validation, provenance, dry-run summaries, and rollback safety.

## Database migration scaffold

Migration files live in `app/backend/database/migrations/`. The current migration, `001_ingestion_metadata.sql`, is a non-destructive scaffold for `ingestion_runs`, `ingestion_source_files`, and `ingestion_issues`. It uses only `CREATE TABLE IF NOT EXISTS` and has not been applied to `app/railyatra.db`.

Run the migration safety check:

```bash
python3 scripts/smoke_migrations.py
```

The check rejects destructive/data-writing SQL and validates the migration against in-memory SQLite without opening the target database. Future migrations must remain non-destructive unless a destructive change is explicitly approved.

Never alter `stations`, `trains`, `train_stops`, or `official_fares` without a database backup and reviewed dry-run report. The planned importer must be idempotent and transactional: create ingestion-run and source-file metadata first, then import normalized railway records only after dry-run approval.

## Git safety rules

- Check `git status --short` before editing and again after validation.
- Back up an existing file before patching it.
- Never commit `frontend/dist/`, generated archives, local databases, virtual environments, `node_modules/`, or temporary backup files.
- After a successful frontend build, remove `frontend/dist/` and any temporary `App.jsx.backup.*` files created for the change.
- Commit frontend changes from the repository root.
- Keep commits focused and review `git diff` before committing.
- Do not modify unrelated user changes in a dirty working tree.
- Do not blindly remove `=======` from `frontend/src/App.jsx`; first confirm it is a standalone merge marker rather than valid text.
- Treat `archive_legacy/` as historical reference only; do not edit it.
- Keep the current ingestion workflow read-only; do not write to `app/railyatra.db` yet.
- Keep migrations non-destructive unless a destructive operation is explicitly approved.
- Back up the database and review a dry-run report before changing core railway or fare tables.

## Recommended next tasks

1. Review and safely apply the ingestion metadata migration only when an explicit apply workflow and backup step exist.
2. Add fixture-based validation for the station, train, and schedule normalizers.
3. Implement an idempotent, transactional importer that writes ingestion metadata first and normalized railway data only after dry-run approval.
4. Record source provenance, checksums, import timestamps, and accepted/rejected row counts.
5. Keep API and frontend behavior unchanged until imported data is validated against the existing smoke suite.

## Backup and Migration Workflow

RailYatra now has a safe database backup and migration workflow.

Commands:

    python3 scripts/backup_database.py
    python3 scripts/run_migrations.py --dry-run
    python3 scripts/run_migrations.py --apply
    scripts/check_all.sh

Rules:

- Always create a backup before any database write.
- Migration runner must default to dry-run.
- Database writes require explicit --apply.
- Backups must not be committed.
- frontend/dist must not be committed.
- archive_legacy/ is historical and must not be edited.
- Existing railway data tables must not be altered without explicit approval.

Current status:

- Non-destructive ingestion metadata migration scaffold exists.
- Migration smoke test is included in combined checks.
- Migration runner dry-run is included in combined checks.
- Existing train/station/route/fare data remains untouched.

## Metadata-Only Ingestion Writer

Current status:

- scripts/write_ingestion_metadata.py exists.
- scripts/smoke_metadata_writer.py exists.
- scripts/check_all.sh includes metadata writer smoke testing.
- Dry-run mode is safe and read-only.
- Apply mode writes only ingestion audit metadata.
- Railway data tables remain untouched.

Commands:

    python3 scripts/write_ingestion_metadata.py --dry-run
    python3 scripts/write_ingestion_metadata.py --apply
    python3 scripts/smoke_metadata_writer.py
    scripts/check_all.sh

## Ingestion Metadata Verifier

Current status:

- scripts/verify_ingestion_metadata.py exists.
- Dry-run mode validates metadata schema in memory.
- scripts/check_all.sh includes verifier dry-run.
- Live mode can verify latest metadata apply result.
- Railway data tables remain untouched.

Commands:

    python3 scripts/verify_ingestion_metadata.py --dry-run
    python3 scripts/verify_ingestion_metadata.py
    scripts/check_all.sh

## Pre-Import Safety Gate

Current status:

- scripts/pre_import_gate.sh exists.
- The gate runs all required safety checks before real import work.
- The gate is dry-run/read-only for railway data.
- The gate removes frontend/dist after frontend build.
- Real railway data tables remain untouched.

Command:

    scripts/pre_import_gate.sh

## Staging Import Dry-Run Planner

Current status:

- scripts/plan_staging_import.py exists.
- scripts/smoke_staging_planner.py exists.
- scripts/check_all.sh includes staging planner smoke test.
- scripts/pre_import_gate.sh includes staging planner smoke test.
- Planner dry-run does not open the database.
- Planner dry-run does not write to the database.
- Planner validates blocking issues before any future staging write.

Commands:

    python3 scripts/plan_staging_import.py --dry-run
    python3 scripts/smoke_staging_planner.py
    scripts/pre_import_gate.sh
    scripts/check_all.sh

## Staging Apply Skeleton

Current status:

- scripts/apply_staging_import.py exists.
- scripts/smoke_staging_apply.py exists.
- scripts/check_all.sh includes staging apply skeleton smoke test.
- scripts/pre_import_gate.sh includes staging apply skeleton smoke test.
- Dry-run mode is safe.
- Apply mode is disabled by design.
- No staging rows are written yet.
- No production railway tables are touched.

Commands:

    python3 scripts/apply_staging_import.py --dry-run
    python3 scripts/smoke_staging_apply.py
    scripts/pre_import_gate.sh
    scripts/check_all.sh

## Phase 2.5 Completed

Phase 2.5 status:

Completed.

RailYatra now has a real railway data safety and staging layer.

Current verified raw data scale:

- stations: 8990
- trains: 5208
- schedules/stops: 417080

Completed systems:

- migration safety
- metadata audit
- true dry-run verifier
- pre-import safety gate
- staging tables
- staging planner
- confirmed staging-only apply mode
- staging import verifier
- combined check pipeline

Main checks:

    scripts/check_all.sh
    scripts/pre_import_gate.sh

Next phase:

Phase 3: connect validated staging railway data into the real search and graph engine.

## Phase 3 Checkpoint

Phase 3 has connected the validated staging railway data to a real route/search layer.

Completed capabilities:

- read-only staging query helpers
- staging health endpoint
- staging station search endpoint
- staging direct-train endpoint
- staging train-stops endpoint
- staging route engine
- production-candidate `/search-v2`
- frontend `/search-v2` route preview
- station suggestions from staging data
- train stop drilldown
- route lookup indexes
- smoke tests for backend, frontend, search-v2, staging API, route engine, and indexes

Legacy `/search` remains protected and unchanged.

See `docs/PHASE_3_STATUS.md` for the full checkpoint.

## Phase 4 Checkpoint

Phase 4 has added a production-candidate recommendation layer on top of the Phase 3 staging route engine.

Completed capabilities:

- `/recommend-v2` endpoint
- recommendation ranking
- route confidence labels
- transfer safety labels
- recommendation reasons
- live booking/fare/availability warning
- frontend recommendation preview
- station suggestions in recommendation preview
- backend recommend-v2 smoke test
- frontend recommend-v2 smoke test

Important safety status:

- legacy `/search` remains unchanged
- `/search-v2` remains available
- `/recommend-v2` is read-only
- live booking is not connected yet
- production railway tables remain protected

See `docs/PHASE_4_STATUS.md` for the full checkpoint.

## Phase 5 Checkpoint

Phase 5 has prepared RailYatra for public beta preview readiness.

Completed capabilities:

- `/product/status` endpoint
- `/product/beta-checklist` endpoint
- frontend product status panel
- frontend public beta checklist panel
- product readiness smoke test
- frontend product readiness smoke test
- beta checklist smoke test
- frontend beta checklist smoke test

Current public beta position:

- real railway route recommendation preview is demo-ready
- user/investor demo is allowed
- live booking claim is blocked
- ticket payment claim is blocked
- PNR, live fare and live availability are not connected yet

Important safety status:

- legacy `/search` remains unchanged
- `/search-v2` remains available
- `/recommend-v2` remains available
- production railway tables remain protected

See `docs/PHASE_5_STATUS.md` for the full checkpoint.

## Phase 6 Checkpoint

Phase 6 has prepared RailYatra for public demo deployment packaging.

Completed capabilities:

- `.env.example`
- backend CORS configuration
- `/product/deployment-status`
- frontend API base via `VITE_RAILYATRA_API_BASE`
- public demo warning banner
- backend `app/requirements.txt`
- Render backend config
- Vercel frontend config
- deployment targets guide
- README quickstart
- public demo script
- public launch checklist
- deployment smoke tests

Current deployment position:

- public demo deployment is ready to start
- local full checks must pass before deployment
- live booking, payment, PNR, live fare and live availability remain blocked

See `docs/PHASE_6_FINAL_CHECKPOINT.md` for the final Phase 6 checkpoint.

## Phase 7 Checkpoint

Phase 7 has started.

Current phase:

- Phase 7: actual public demo deployment stage

Completed in this step:

- Phase 7 deployment runbook
- deployed public demo smoke checker
- deployed smoke checker safely skips until backend/frontend URLs are provided
- deployed smoke checker verifies backend safety flags after deployment

Next manual deployment work:

- push repository to GitHub
- deploy backend on Render
- deploy frontend on Vercel
- set frontend backend URL
- set backend allowed origin
- run deployed smoke test with real deployed URLs

## Phase 7 Deployment Preflight

Current phase:

- Phase 7: actual public demo deployment

Added in this step:

- `scripts/deploy_preflight.sh`
- `docs/PHASE_7_MANUAL_DEPLOYMENT_STEPS.md`
- `scripts/smoke_phase7_deploy_preflight.py`

Next action after this commit:

- run `scripts/deploy_preflight.sh`
- push repo to GitHub
- deploy backend on Render
- deploy frontend on Vercel
- run deployed smoke test with deployed URLs

## Phase 7 Local Deploy Ready Checkpoint

Current phase:

- Phase 7: actual public demo deployment

This checkpoint confirms the project is ready for GitHub push after local preflight passes.

Use:

- `scripts/deploy_preflight.sh`
- `scripts/github_push_readiness.sh`

Next action:

- if origin remote exists, run `git push -u origin main`
- if origin remote is missing, create an empty GitHub repo and add remote first
- after GitHub push, deploy backend on Render and frontend on Vercel

