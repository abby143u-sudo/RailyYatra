# RailYatra Phase 16 Public Beta Checklist

Status: READY FOR CONTROLLED PUBLIC BETA

Live URLs:

- Frontend: https://raily-yatra.vercel.app
- Backend: https://railyyatra-backend.onrender.com

Beta-ready items:

- Live frontend is deployed on Vercel.
- Live backend is deployed on Render.
- Backend health responds.
- Route search responds for PNBE to NDLS.
- Route response includes safe train_no and train_name fields.
- Feedback API is available.
- Analytics API is available.
- Admin auth is protected with RAILYATRA_ADMIN_TOKEN.
- Admin audit logs are available.
- Public product boundary is clear.

Product boundary:

- RailYatra is currently a railway route recommendation preview.
- Live ticket booking is not connected yet.
- Payment is not connected yet.
- PNR is not connected yet.
- Live seat availability is not connected yet.
- Live fare is not connected yet.
- Live train status needs an official or licensed provider API.

Manual QA checklist:

1. Open https://raily-yatra.vercel.app
2. Hard refresh with Cmd + Shift + R.
3. Search PNBE to NDLS.
4. Confirm page does not blank.
5. Confirm at least one route result appears.
6. Search NDLS to PNBE.
7. Confirm beta readiness panel appears.
8. Open https://raily-yatra.vercel.app/?admin=preview
9. Paste admin token.
10. Confirm feedback, analytics and audit logs load.

Next phase:

Phase 17: real railway data quality, route scoring, station autocomplete polish and investor demo deck.
