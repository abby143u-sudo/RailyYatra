# RailYatra Phase 10 Backend API Smoke Test

Status: ADDED

Script:
scripts/smoke_phase10_backend_api.py

Tested endpoints:
- GET /health
- GET /feedback/health
- POST /feedback
- GET /feedback
- GET /analytics/health
- POST /analytics/event
- GET /analytics/events

Usage:
RAILYATRA_BACKEND_URL=https://railyyatra-backend.onrender.com python3 scripts/smoke_phase10_backend_api.py

Note:
If deployed smoke fails right after pushing, wait for Render redeploy to finish.
