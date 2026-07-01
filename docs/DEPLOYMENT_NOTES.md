# RailYatra Deployment Notes

## Current deployment target

RailYatra is currently prepared for a public beta preview deployment, not a live railway booking product.

## Local backend

Run from project root:

    cd app
    uvicorn backend.api.main:app --reload

Expected backend:

    http://127.0.0.1:8000

Useful endpoints:

- `/`
- `/health`
- `/search`
- `/search-v2`
- `/recommend-v2`
- `/product/status`
- `/product/beta-checklist`
- `/product/deployment-status`

## Local frontend

Run from project root:

    npm --prefix frontend run dev

Expected frontend:

    http://localhost:5173

## Environment variables

Copy:

    cp .env.example .env

Important defaults:

- live booking: disabled
- live fare: disabled
- live availability: disabled
- PNR: disabled
- payment: disabled

## Safety

Do not claim:

- official railway booking
- live seat availability
- live fare
- PNR
- payment-enabled ticketing
- cancellation

Allowed public label:

    Real railway route recommendation preview

## Required checks before deployment

Run:

    scripts/check_all.sh
    scripts/pre_import_gate.sh

Expected:

- both pass
- `frontend/dist` is removed before commit
- production railway tables remain protected
- live booking claim remains blocked

## Frontend backend URL

The frontend no longer depends on hardcoded `127.0.0.1` inside each component.

Local default:

    VITE_RAILYATRA_API_BASE=http://127.0.0.1:8000

For deployed frontend, set this variable in Vercel/Netlify:

    VITE_RAILYATRA_API_BASE=https://your-backend-domain.example.com

After changing the variable, rebuild/redeploy the frontend.

## Deployment packaging

Files added for public demo deployment:

- `app/requirements.txt`
- `render.yaml`
- `frontend/vercel.json`
- `docs/DEPLOYMENT_TARGETS.md`

Recommended setup:

- backend on Render
- frontend on Vercel
- frontend env var: `VITE_RAILYATRA_API_BASE`
- backend env var: `RAILYATRA_ALLOWED_ORIGINS`

Keep all live booking/payment/PNR/fare/availability flags disabled until official integrations exist.

## Public demo documents

Before sharing a public link, review:

- README.md
- docs/PUBLIC_DEMO_SCRIPT.md
- docs/LAUNCH_CHECKLIST.md
- docs/PUBLIC_BETA_READINESS.md

The approved public label remains:

    Real railway route recommendation preview
