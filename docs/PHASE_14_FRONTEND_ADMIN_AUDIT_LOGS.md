# RailYatra Frontend Admin Audit Logs

Status: ADDED

Added:

- Protected admin dashboard token loading flow
- Admin audit logs table
- Admin auth status card
- Audit log count card
- Feedback and analytics tables remain available after token auth

Behavior:

- If admin token is missing, dashboard asks for token.
- Token is stored only in browser sessionStorage.
- Token is sent as X-RailYatra-Admin-Token.
- No token is committed to GitHub or exposed in frontend source.

Preview URL:

https://raily-yatra.vercel.app/?admin=preview

Next:

Deploy frontend through Vercel and verify protected admin dashboard UI.

## Live verified

Frontend admin audit dashboard is verified on live Vercel frontend.

Verified:

- Protected admin token flow
- Audit logs table UI
- Live frontend JS contains protected admin dashboard code
- Backend protected admin token works
- Local frontend build passes

Next: Phase 15 beta polish.

