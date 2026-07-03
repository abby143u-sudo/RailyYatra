# RailYatra Vercel CORS Hard Fix

Status: ADDED

Problem:

Live Vercel frontend could reach the page but browser API calls still showed backend connection issue.

Likely cause:

Browser CORS/preflight blocking, even though terminal curl showed backend is live.

Fix:

- Added app/backend/api/cors_public_middleware.py
- Allows https://raily-yatra.vercel.app
- Allows local frontend origins
- Handles OPTIONS preflight requests
- Allows X-RailYatra-Admin-Token header for protected admin dashboard

Next:

Deploy latest commit on Render backend, then hard refresh Vercel frontend with Cmd + Shift + R.
