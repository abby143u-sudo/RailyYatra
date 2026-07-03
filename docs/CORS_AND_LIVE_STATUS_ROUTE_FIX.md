# RailYatra CORS and Live Status Route Fix

Status: FIXED

Problem seen in Chrome console:

- Browser blocked backend fetch because Access-Control-Allow-Origin header was missing.
- /live-status/health returned 404.

Fix:

- Added official FastAPI CORSMiddleware for Vercel frontend.
- Allowed X-RailYatra-Admin-Token header.
- Added /live-status/health endpoint.
- Added /live-status endpoint with no-fake-live-status boundary.

After deploy:

- Render backend must be redeployed.
- Browser hard refresh required: Cmd + Shift + R.
