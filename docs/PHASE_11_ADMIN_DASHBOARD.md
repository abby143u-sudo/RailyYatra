# RailYatra Phase 11 Admin Dashboard

Status: STARTED

Added:

- frontend/src/components/AdminDashboardPreviewPanel.jsx
- Admin summary preview connected to /admin/demo-summary
- Feedback count card
- Analytics count card
- Product boundary card
- Feedback type JSON preview
- Analytics type JSON preview

Production note:

When RAILYATRA_ADMIN_TOKEN is enabled on Render, this panel should move behind protected admin login and should not be exposed publicly.

Next Phase 11 targets:

1. Admin dashboard route/page separation
2. Admin token/login design
3. Feedback inbox table
4. Analytics event table
5. Managed PostgreSQL migration plan implementation

## Admin route gate

Admin dashboard preview is now separated from the public homepage.

Preview URLs:

- http://127.0.0.1:5173/?admin=preview
- http://127.0.0.1:5173/#admin
- https://raily-yatra.vercel.app/?admin=preview

The public homepage hides admin preview by default.

## Analytics event table

Added latest analytics event table to the admin dashboard preview.

The table reads from /admin/demo-summary and shows event type, details, timestamp and page.

Next target: admin token input or protected login design.

## Admin token input

Added browser-session admin token input to the admin dashboard preview.

Behavior:

- Token is stored only in sessionStorage.
- Token is sent as X-RailYatra-Admin-Token.
- If backend returns 401, the panel asks for the admin token.

Next target: managed PostgreSQL migration implementation plan or final admin dashboard QA.

## Admin dashboard QA

Phase 11 admin dashboard preview QA completed.

Verified:

- Admin preview route gate
- Admin token input
- Feedback inbox
- Analytics event table
- Frontend production build
- Live frontend response

Next target: managed PostgreSQL migration implementation plan.

