# RailYatra Phase 11 Admin Route Gate

Status: ADDED

Goal:
Separate admin preview from the public homepage.

Added:

- frontend/src/components/AdminDashboardGate.jsx
- AdminDashboardPreviewPanel now renders only when admin preview mode is enabled.

Preview URLs:

- Local: http://127.0.0.1:5173/?admin=preview
- Local alternative: http://127.0.0.1:5173/#admin
- Live: https://raily-yatra.vercel.app/?admin=preview

Public homepage behavior:

- Admin dashboard preview is hidden by default.
- Public demo remains focused on route recommendation.

Production note:

This is frontend route gating only. Real production admin access must use backend auth and protected admin login.

Next Phase 11 targets:

1. Feedback inbox table
2. Analytics event table
3. Admin token input or protected login design
4. Managed PostgreSQL migration implementation plan
