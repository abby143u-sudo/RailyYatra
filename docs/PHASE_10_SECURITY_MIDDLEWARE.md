# RailYatra Phase 10 Security Middleware

Status: ADDED

Added backend security foundation:

- Basic in-memory request rate-limit
- Stricter write request limit for POST, PUT, PATCH and DELETE
- Optional admin token protection
- Standard JSON error envelope for security failures

Admin protection behavior:

- If RAILYATRA_ADMIN_TOKEN is not set, admin endpoints remain open for current demo testing.
- If RAILYATRA_ADMIN_TOKEN is set, /admin endpoints require X-RailYatra-Admin-Token or Authorization Bearer token.

Smoke script:

- scripts/smoke_phase10_security_middleware.py
