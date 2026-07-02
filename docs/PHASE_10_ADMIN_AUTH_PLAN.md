# RailYatra Admin Authentication Plan

Status: PLANNED

Current state:

- Admin summary endpoints exist.
- Security middleware supports optional admin token protection.
- If RAILYATRA_ADMIN_TOKEN is set, /admin endpoints require a token.

Immediate safe setup:

Set this Render environment variable:

RAILYATRA_ADMIN_TOKEN=<strong-secret-token>

Allowed request formats:

1. X-RailYatra-Admin-Token header
2. Authorization: Bearer <token>

Admin endpoint protection target:

- /admin/health
- /admin/feedback-summary
- /admin/analytics-summary
- /admin/demo-summary

Recommended admin auth phases:

Phase A: Token protection
- Use RAILYATRA_ADMIN_TOKEN on Render.
- Keep admin dashboard private.
- Use token only from local/internal tools.

Phase B: Admin login
- Create admin_users table.
- Add password hash or OAuth login.
- Add JWT session.
- Add role field: owner, admin, support.

Phase C: Audit logs
- Log admin reads and actions.
- Store timestamp, admin id, endpoint, action and IP.

Phase D: Production dashboard
- Protected admin UI.
- Feedback inbox.
- Analytics dashboard.
- Route quality reports.
- Live integration monitoring.

Security rule:

Never expose admin token in frontend public code. Admin token must stay in backend env or local terminal only.
