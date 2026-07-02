# RailYatra Phase 9 — Product Hardening

Status: STARTED

Live frontend:
https://raily-yatra.vercel.app

Live backend:
https://railyyatra-backend.onrender.com

Phase 9 goal:
Move from stable public demo to product hardening.

Started items:

- User feedback capture panel
- Browser-local feedback storage
- Feedback categories for bug, route quality, UI and product ideas

Upcoming items:

1. Demo analytics event tracking
2. Saved demo searches
3. Better route result explanation
4. Feedback export option
5. Live integration planning docs
6. Production readiness checklist

Current boundary:
RailYatra remains a real railway route recommendation preview. Live booking, payment, PNR, live fare and live seat availability are not connected yet.

## Demo analytics foundation

Added browser-local demo analytics through PublicDemoAnalyticsPanel.

Tracked events:

- page_view
- main_search_submit

This is intentionally local-only for the public demo. Production analytics can be connected later after deciding privacy, consent and measurement needs.

