# RailYatra Train Number UI Crash Fix

Status: FIXED

Problem:

Live frontend crashed with Cannot read properties of undefined reading train_no.

Fix:

- Backend fallback route now returns train_no at route, leg and train-object levels.
- trains array now contains train objects instead of plain strings.
- segments array mirrors legs for frontend compatibility.
- primary_train fields added.
- Frontend train_no reads made safer.

Next:

Deploy latest commit on Render backend and let Vercel deploy frontend, then hard refresh browser.
