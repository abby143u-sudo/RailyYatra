# RailYatra Project Status

Last reviewed: 30 June 2026

## Current status

RailYatra is a FastAPI and React/Vite application for finding alternate train routes and generating smart journey recommendations. The active backend entry point is `app/backend/api/main.py`; the active frontend is primarily implemented in `frontend/src/App.jsx` and `frontend/src/App.css`.

The frontend production build currently passes. The working tree was clean before this document was created. Recent commits have focused on route-search usability, validation, loading and empty states, route details, transfer safety, and booking guidance.

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

Existing backend functional check:

```bash
cd ~/RailYatra/app 2>/dev/null || cd ~/railyatra/app
python check_backend.py
```

Dedicated frontend and backend smoke-test scripts are not yet present. The backend smoke test should cover `/`, `/health`, and `/search`.

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

## Recommended next tasks

1. Add a frontend smoke-test script.
2. Add a backend smoke-test script for `/`, `/health`, and `/search`.
3. Update the project README with the verified run and validation commands.
4. Add an app-version badge and build-information card.
5. Refactor `frontend/src/App.jsx` gradually, with a clean build after each small change.

