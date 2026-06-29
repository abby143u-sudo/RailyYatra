# RailYatra Stabilization Checkpoint

Checkpoint date: 30 June 2026

## Repository status

The `main` branch was clean at the start of this checkpoint. Frontend and backend source code were not changed. The combined smoke suite passed before this document was created:

- Backend smoke test: 4 passed, 0 skipped
- Frontend production build: passed
- Generated `frontend/dist/`: removed after validation

The active backend entry point remains `app/backend/api/main.py`. The inactive legacy backend at `archive_legacy/api.py` must not be edited.

## Latest commits

Recent stabilization work on `main`:

| Commit | Change |
| --- | --- |
| `5e141b6` | Add project gitignore rules |
| `48c8c51` | Add combined smoke check |
| `98ff637` | Add project run and test instructions |
| `bcaa193` | Add frontend smoke test |
| `d8c17aa` | Add backend smoke test |
| `88c5bb0` | Add project status documentation |
| `b6ce9ba` | Add clean no results card |
| `1c47bc8` | Add route skeleton loader |
| `a587fb4` | Add station code helper panel |
| `901a01e` | Add search form validation |

## Smoke test commands

Run all checks from the repository root:

```bash
./scripts/check_all.sh
```

Run the checks separately when diagnosing a failure:

```bash
python3 scripts/smoke_backend.py
./scripts/smoke_frontend.sh
```

The backend smoke test requires FastAPI `TestClient` dependencies, including `httpx`, in the active Python environment. The frontend smoke test builds the application and removes `frontend/dist/` afterward.

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

The next development phase should strengthen the data foundation before adding more route-search UI features.

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

The first implementation milestone should be a documented ingestion contract plus a small, licensed fixture dataset that can be imported repeatedly with deterministic results.

## Safety rules for the next phase

- Keep imports out of request handlers; use dedicated scripts or services.
- Back up the local database before schema migrations or large imports.
- Never commit local databases, raw restricted datasets, credentials, `frontend/dist/`, or backup files.
- Review `git status --short` and run `./scripts/check_all.sh` before each commit.
- Continue to leave `archive_legacy/api.py` untouched.
