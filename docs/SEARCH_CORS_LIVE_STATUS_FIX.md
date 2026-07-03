# RailYatra Search CORS Live Status Fix

Status: FIXED

Fixed:

- Legacy /search 500 caused by stop_order column mismatch
- Backend graph code now uses stop_sequence
- Deploy database script now also creates stop_order compatibility column
- Added /live-status/health endpoint
- Added /live-status endpoint with no-fake-live-status boundary
- Added hard CORS support for Vercel frontend

Browser issue:

The frontend red backend warning was caused by backend /search crashing and missing live-status route. CORS headers are now also included for Vercel.

Next:

Deploy latest commit on Render backend, then hard refresh Vercel frontend with Cmd + Shift + R.
