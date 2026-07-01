# RailYatra Deployment Targets

## Recommended simple public demo setup

Backend:

- Render web service
- Python environment
- Root directory: `app`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`

Frontend:

- Vercel
- Framework: Vite
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`

## Required frontend environment variable

Set this in Vercel after backend deployment:

    VITE_RAILYATRA_API_BASE=https://your-render-backend-url.onrender.com

## Required backend environment variable

Set this in Render after frontend deployment:

    RAILYATRA_ALLOWED_ORIGINS=https://your-vercel-frontend-url.vercel.app

For local development:

    RAILYATRA_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

## Important live feature flags

Keep these false until official integrations exist:

    RAILYATRA_LIVE_BOOKING_ENABLED=false
    RAILYATRA_LIVE_FARE_ENABLED=false
    RAILYATRA_LIVE_AVAILABILITY_ENABLED=false
    RAILYATRA_PNR_ENABLED=false
    RAILYATRA_PAYMENT_ENABLED=false

## Backend health checks after deploy

Open these URLs after backend deployment:

- `/`
- `/health`
- `/product/status`
- `/product/beta-checklist`
- `/product/deployment-status`
- `/recommend-v2?source=LTT&destination=VVH&direct_limit=3&transfer_limit=1`

## Frontend checks after deploy

Open the deployed frontend and confirm:

- public demo warning banner is visible
- product status panel loads
- beta checklist panel loads
- recommend-v2 panel returns recommendations
- station suggestions work
- no live booking/payment/PNR claim is shown

## Public demo label

Use:

    Real railway route recommendation preview

Do not use:

- official railway booking app
- live booking app
- payment-enabled ticketing app
- PNR app
- live seat availability app
