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
python3 scripts/smoke_ingestion.py
python3 scripts/import_railway_data.py --dry-run
python3 scripts/import_railway_data.py --dry-run --report-json
```

Combined project check:

```bash
scripts/check_all.sh
```

The combined check covers the backend API, railway data inspection, dry-run import CLI, and frontend production build. It removes `frontend/dist/` after validation.

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

## Git safety rules

- Check `git status --short` before editing and again after validation.
- Back up an existing file before patching it.
- Never commit `frontend/dist/`, generated archives, local databases, virtual environments, `node_modules/`, or temporary backup files.
- After a successful frontend build, remove `frontend/dist/` and any temporary `App.jsx.backup.*` files created for the change.
- Commit frontend changes from the repository root.
- Keep commits focused and review `git diff` before committing.
- Do not modify unrelated user changes in a dirty working tree.
- Do not blindly remove `=======` from `frontend/src/App.jsx`; first confirm it is a standalone merge marker rather than valid text.
- Do not edit `archive_legacy/api.py`.
- Keep the current ingestion workflow read-only; do not write to `app/railyatra.db` yet.

## Recommended next tasks

1. Design a non-destructive schema migration for ingestion metadata and missing railway fields.
2. Add fixture-based validation for the station, train, and schedule normalizers.
3. Implement idempotent, transactional imports with explicit dry-run and rollback behavior.
4. Record source provenance, checksums, import timestamps, and accepted/rejected row counts.
5. Keep API and frontend behavior unchanged until imported data is validated against the existing smoke suite.
