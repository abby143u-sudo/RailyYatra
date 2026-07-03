# RailYatra Phase 13 Admin Auth and Audit Logs

Status: STARTED

Added:

- app/backend/api/admin_auth.py
- app/backend/api/admin_audit.py
- GET /admin/auth-status
- GET /admin/audit-logs
- scripts/smoke_phase13_admin_auth_audit.py

Admin protection behavior:

- If RAILYATRA_ADMIN_TOKEN is not set, admin APIs stay open for preview mode.
- If RAILYATRA_ADMIN_TOKEN is set, admin APIs require X-RailYatra-Admin-Token or Authorization: Bearer token.
- Token value is never returned by the API.
- Token must stay in Render backend environment variables only.

Audit log behavior:

- Admin auth status reads are logged.
- Admin audit log reads are logged.
- PostgreSQL is used when DATABASE_URL exists.
- SQLite fallback is used locally when DATABASE_URL is missing.

Next:

Deploy latest commit on Render and verify Phase 13 smoke script against live backend.

## NameError fix

Admin API was rewritten cleanly to ensure all admin routes have explicit imports and stable endpoint definitions.

Verified locally:

- /admin/auth-status
- /admin/audit-logs
- Phase 13 admin auth audit smoke
- Phase 10 admin smoke
- Frontend production build

Next: deploy latest commit on Render and verify live Phase 13 smoke.

