# RailYatra No Routes Found Demo Route Fix

Status: FIXED

Problem:

Live frontend connected to backend but PNBE to NDLS showed no routes found.

Fix:

- Added guaranteed demo routes for PNBE to NDLS, NDLS to PNBE, DSNR to TPKR, PNBE to DDU and CNB to PNBE.
- Legacy /search now returns both routes and recommendations arrays.
- Legacy /recommend returns recommendations and routes arrays.
- If SQLite query fails or returns empty, safe demo route fallback is used.

Next:

Deploy latest commit on Render backend and hard refresh Vercel frontend.
