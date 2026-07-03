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

## Frontend stability note

The main top From/To autocomplete is temporarily disabled to keep the public demo stable. Manual station-code entry works, and the next safe step is to rebuild autocomplete as an isolated tested component.

## Phase 8 stable public demo release

RailYatra Phase 8 stable public demo release is ready.

Frontend: https://raily-yatra.vercel.app

Backend: https://railyyatra-backend.onrender.com

Main From/To search uses SafeStationInput. PNBE and NDLS typing should not blank the page.

Next phase: Phase 9 — analytics, user feedback capture, saved searches, and live integration planning.

## Phase 9

Phase 9 has started: product hardening, user feedback capture, demo analytics, saved demo searches and live integration planning.

First Phase 9 feature: public feedback capture panel with browser-local storage.

## Phase 9 QA

Phase 9 product hardening QA checkpoint completed.

Completed: feedback capture/export, browser-local analytics, saved demo searches, production readiness checklist, live integration planning, route explanation panel and SafeStationInput main autocomplete.

Next phase: Phase 10 — backend hardening, real feedback API, analytics API, authentication/admin layer and live integration architecture.

## Phase 10

Phase 10 has started: backend hardening, real feedback API, analytics API, admin/internal endpoints, request validation, error envelopes, authentication planning and live integration architecture.

First target: move feedback from browser-local storage to a backend feedback API.

## Phase 10 Backend APIs Verified

Phase 10 backend APIs are verified on the deployed Render backend: feedback, analytics and admin summary APIs. Smoke scripts are available for deployed checks.

Next: request validation, standard API error envelope, rate-limit planning and admin protection planning.

## Phase 10 Validation Verified

Phase 10 standard API error envelope is verified on the deployed Render backend. Feedback, analytics and admin smoke tests also pass after the validation layer.

Next: rate-limit planning and admin protection planning.

## Phase 10 Security Verified

Phase 10 security middleware is verified on the deployed Render backend. Security smoke, error envelope smoke, backend smoke and admin smoke all pass.

Next: database persistence upgrade for feedback and analytics.

## Phase 10 Production Plan

Production database and admin authentication planning docs have been added. Next target: verify deployed SQLite persistence, set/admin-token planning, final Phase 10 QA and Phase 10 final checkpoint.

## Phase 10 Final QA

Phase 10 final QA checkpoint is complete. Feedback, analytics, admin summary, error envelope, security middleware and SQLite persistence are verified through deployed smoke tests.

Next: Phase 11 admin dashboard and managed PostgreSQL migration.

## Phase 11 Admin Dashboard Started

Phase 11 has started with an admin dashboard preview connected to the backend admin summary API. Next: protected admin route, feedback inbox, analytics table and managed PostgreSQL migration.

## Phase 11 Admin Dashboard QA

Phase 11 admin dashboard preview QA is complete. The admin preview is gated behind ?admin=preview, includes admin token input, feedback inbox and analytics event table.

Next: managed PostgreSQL migration implementation plan.

## Phase 11 PostgreSQL Migration Plan

Managed PostgreSQL migration planning has been added along with a backend database status endpoint at /admin/database-status. Next: verify deployed database status and complete Phase 11 QA.

## Phase 12 Managed PostgreSQL Support Started

Phase 12 has started with hybrid managed PostgreSQL support. Feedback and analytics can use DATABASE_URL when configured, while SQLite remains the fallback for local development.

Next: deploy verification in SQLite fallback mode, then create/set managed PostgreSQL DATABASE_URL on Render.

## Phase 12 SQLite Fallback Verified

Phase 12 SQLite fallback mode is verified on the deployed Render backend. The app can now run without DATABASE_URL and is ready for the next step: managed PostgreSQL setup on Render.

## Phase 12 PostgreSQL Live Verified

Phase 12 is verified: the Render backend now uses managed PostgreSQL through DATABASE_URL for feedback and analytics persistence, while SQLite remains the local fallback.

Next: Phase 13 protected admin auth and audit logs.

