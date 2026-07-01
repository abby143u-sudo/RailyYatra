# RailYatra Phase 7 Deployment Runbook

Phase 7 goal:

Deploy RailYatra public demo preview and verify deployed links.

## Current phase

We are now in Phase 7: actual deployment stage.

Phase 6 completed deployment packaging. Phase 7 performs real deployment actions.

## Deployment stack

- Backend: Render
- Frontend: Vercel

## Approved public label

Real railway route recommendation preview

## Do not claim

- live booking
- official railway booking
- live seat availability
- live fare
- PNR
- payment
- cancellation

## Before deploying

Run locally:

    scripts/check_all.sh
    scripts/pre_import_gate.sh

Both must pass.

## Backend deployment on Render

Use these settings:

- Root directory: app
- Build command: pip install -r requirements.txt
- Start command: uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT

Backend environment variables:

    RAILYATRA_ENV=production
    RAILYATRA_ALLOWED_ORIGINS=https://your-vercel-frontend-url.vercel.app
    RAILYATRA_LIVE_BOOKING_ENABLED=false
    RAILYATRA_LIVE_FARE_ENABLED=false
    RAILYATRA_LIVE_AVAILABILITY_ENABLED=false
    RAILYATRA_PNR_ENABLED=false
    RAILYATRA_PAYMENT_ENABLED=false

## Frontend deployment on Vercel

Use these settings:

- Root directory: frontend
- Framework: Vite
- Build command: npm run build
- Output directory: dist

Frontend environment variable:

    VITE_RAILYATRA_API_BASE=https://your-render-backend-url.onrender.com

## After backend deploy

Check these URLs:

- /
- /health
- /product/status
- /product/beta-checklist
- /product/deployment-status
- /recommend-v2?source=LTT&destination=VVH&direct_limit=3&transfer_limit=1

## After frontend deploy

Open frontend and confirm:

- public beta warning banner visible
- product status panel loads
- beta checklist panel loads
- recommend-v2 panel works
- station suggestions work
- no live booking/payment/PNR claim visible

## Deployed smoke command

After deployment, run:

    RAILYATRA_DEPLOYED_BACKEND_URL=https://your-render-backend-url.onrender.com RAILYATRA_DEPLOYED_FRONTEND_URL=https://your-vercel-frontend-url.vercel.app python3 scripts/smoke_deployed_public_demo.py

If URLs are not set, the deployed smoke test skips safely during local development.
