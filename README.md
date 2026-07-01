# RailYatra

RailYatra is a real railway route recommendation preview.

It can currently demonstrate:

- real railway staging-data route search
- ranked route recommendations
- confidence labels
- transfer safety labels
- station suggestions
- train stop drilldown
- product status checks
- public beta readiness checks

It is not a live railway ticket booking product yet.

Do not claim:

- live ticket booking
- payment-enabled ticketing
- official railway booking
- live seat availability
- live fare
- PNR
- cancellation

Recommended public demo label:

Real railway route recommendation preview

## Local quickstart

Backend:

    cd app
    uvicorn backend.api.main:app --reload

Frontend:

    npm --prefix frontend run dev

Backend default:

    http://127.0.0.1:8000

Frontend default:

    http://localhost:5173

## Important endpoints

- /
- /health
- /search
- /search-v2
- /recommend-v2
- /product/status
- /product/beta-checklist
- /product/deployment-status
- /staging/health
- /staging/stations
- /staging/direct
- /staging/search
- /staging/trains/{train_number}/stops

## Required checks before demo

Run:

    scripts/check_all.sh
    scripts/pre_import_gate.sh

Expected:

- both pass
- frontend builds successfully
- frontend/dist is removed before commit
- production railway tables remain protected
- live booking/payment/PNR claims remain blocked

## Deployment

Recommended public demo setup:

- backend on Render
- frontend on Vercel

Frontend environment variable:

    VITE_RAILYATRA_API_BASE=https://your-backend-domain.example.com

Backend environment variable:

    RAILYATRA_ALLOWED_ORIGINS=https://your-frontend-domain.example.com

Live feature flags must stay disabled until official integrations exist:

    RAILYATRA_LIVE_BOOKING_ENABLED=false
    RAILYATRA_LIVE_FARE_ENABLED=false
    RAILYATRA_LIVE_AVAILABILITY_ENABLED=false
    RAILYATRA_PNR_ENABLED=false
    RAILYATRA_PAYMENT_ENABLED=false

## Current project docs

- docs/PHASE_5_STATUS.md
- docs/PHASE_6_STATUS.md
- docs/PUBLIC_BETA_READINESS.md
- docs/DEPLOYMENT_NOTES.md
- docs/DEPLOYMENT_TARGETS.md
- docs/PUBLIC_DEMO_SCRIPT.md
- docs/LAUNCH_CHECKLIST.md

## Live public demo

Frontend: https://raily-yatra.vercel.app

Backend: https://railyyatra-backend.onrender.com

Public label: RailYatra — Real railway route recommendation preview

Safety note: This is not a live ticket booking service yet. Live booking, payment, PNR, live fare, live seat availability and cancellation are not connected.

## Phase 8

Phase 8 has started: Public demo polish, landing page clarity, main search UX, mobile layout and investor/demo flow.

Current live demo:

- Frontend: https://raily-yatra.vercel.app
- Backend: https://railyyatra-backend.onrender.com

Public label: RailYatra — Real railway route recommendation preview

## Phase 8 QA

Phase 8 public demo polish and QA checkpoint completed.

Live frontend: https://raily-yatra.vercel.app

Live backend: https://railyyatra-backend.onrender.com

Recommended demo route: DSNR → TPKR

Next phase: Phase 9 — product hardening, analytics, user feedback capture, saved demo searches, and live integration planning.

