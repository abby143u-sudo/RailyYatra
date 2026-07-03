# RailYatra Frontend Train Name Crash Fix

Status: FIXED

Problem:

Route search UI recovered with error: Cannot read properties of undefined reading train_name.

Fix:

- Added frontend/src/utils/routeNormalize.js.
- Search payloads are normalized before rendering.
- Route, train, leg and segment objects always get safe train_name and train_no fields.
- Common direct train_name reads in App.jsx are guarded.

Next:

Wait for Vercel auto deploy, then hard refresh browser with Cmd + Shift + R.
