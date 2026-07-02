# RailYatra Phase 8 Stable Public Demo Release

Status: STABLE PUBLIC DEMO RELEASE

Frontend:
https://raily-yatra.vercel.app

Backend:
https://railyyatra-backend.onrender.com

Public label:
RailYatra — Real railway route recommendation preview

Stability decisions:

- Main From/To search now uses SafeStationInput.
- Old crashing suggestion panel has been replaced.
- Temporary SafeStationLookupTest was removed from the public page.
- PNBE and NDLS typing should not blank the page.
- Public demo remains preview-only, not a live booking product.

Verified checks:

- Local frontend build passes.
- Live backend health passes.
- Live staging health passes.
- Recommend v2 passes.
- Live frontend metadata responds.
- Deployed smoke script passes.

Manual browser QA:

1. Open https://raily-yatra.vercel.app
2. Hard refresh with Command + Shift + R.
3. In main From box, type PNBE.
4. In main To box, type NDLS.
5. Page should not blank.
6. Try DSNR to TPKR for demo route.

Next phase:
Phase 9 — analytics, user feedback capture, saved searches, and live integration planning.
