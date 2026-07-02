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

