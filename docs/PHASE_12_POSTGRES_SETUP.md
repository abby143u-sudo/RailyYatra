# RailYatra Phase 12 PostgreSQL Setup

Status: SCRIPT ADDED

Added scripts:

- scripts/migrate_phase12_postgres_demo_store.py
- scripts/check_phase12_postgres_readiness.py

Migration script creates:

- feedback
- analytics_events
- admin_audit_logs
- indexes for created_at and type fields

Local behavior:

- If DATABASE_URL is missing, migration script exits safely and keeps SQLite fallback mode.

Render setup steps:

1. Create a managed PostgreSQL database.
2. Copy its internal/external connection URL.
3. Set DATABASE_URL on the Render backend service only.
4. Redeploy backend.
5. Run:

RAILYATRA_BACKEND_URL=https://railyyatra-backend.onrender.com RAILYATRA_EXPECTED_DB_MODE=postgresql python3 scripts/check_phase12_postgres_readiness.py

6. Run full smoke tests:

RAILYATRA_BACKEND_URL=https://railyyatra-backend.onrender.com python3 scripts/smoke_phase10_backend_api.py
RAILYATRA_BACKEND_URL=https://railyyatra-backend.onrender.com python3 scripts/smoke_phase10_admin_api.py

Build command option after DATABASE_URL is set:

pip install -r requirements.txt && python -u scripts/prepare_deploy_database.py && python -u scripts/migrate_phase12_postgres_demo_store.py

Security:

DATABASE_URL must stay in backend environment variables only. Do not expose it in frontend code or Vercel env.
