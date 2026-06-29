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

## Health endpoint

With the backend running, open:

```text
http://127.0.0.1:8000/health
```

`GET /health` reports the backend health status and record counts for trains, stations, and train stops.

## Important project rules

- Do not edit `archive_legacy/api.py`; it is an inactive legacy backend file.
- Do not commit `frontend/dist/` or temporary backup files.
- Check `git status --short` before and after making changes.
- Run the relevant smoke tests before committing.
