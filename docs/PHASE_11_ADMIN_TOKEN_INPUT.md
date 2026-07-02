# RailYatra Phase 11 Admin Token Input

Status: ADDED

Added:

- Admin token input inside admin preview
- Token stored only in browser sessionStorage
- Token sent as X-RailYatra-Admin-Token header
- Clear token button
- 401 handling message when backend requires token

Preview URLs:

- Local: http://127.0.0.1:5173/?admin=preview
- Live: https://raily-yatra.vercel.app/?admin=preview

Important security rule:

The admin token is not stored in source code and must not be exposed in public frontend environment variables.

Backend protection:

Set RAILYATRA_ADMIN_TOKEN on Render to protect /admin endpoints.

Next Phase 11 target:

Managed PostgreSQL migration implementation plan or final admin dashboard QA.
