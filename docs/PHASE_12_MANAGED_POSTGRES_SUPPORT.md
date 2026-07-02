# RailYatra Phase 12 Managed PostgreSQL Support

Status: STARTED

Goal:
Add managed PostgreSQL support while keeping SQLite fallback for local development and demo mode.

Added:

- Hybrid demo store in app/backend/api/demo_store.py
- PostgreSQL mode when DATABASE_URL or RAILYATRA_DEMO_DATABASE_URL is configured
- SQLite fallback when no database URL is configured
- Database status now reports actual runtime store mode
- Feedback and analytics health endpoints report storage mode
- Phase 12 database mode check script

Runtime behavior:

- No DATABASE_URL: use SQLite fallback
- DATABASE_URL=postgresql://...: use managed PostgreSQL

Supported tables:

- feedback
- analytics_events

Environment variables:

- DATABASE_URL
- RAILYATRA_DEMO_DATABASE_URL

Smoke script:

- scripts/check_phase12_managed_database_mode.py

Production setup still required:

1. Create managed PostgreSQL instance.
2. Set DATABASE_URL on Render backend.
3. Redeploy backend.
4. Run Phase 12 database mode check expecting postgresql.
5. Run backend smoke and admin smoke.

Important:
DATABASE_URL must stay in backend environment variables only. Never put it in frontend code.
