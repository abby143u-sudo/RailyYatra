# RailYatra Public Demo Launch Checklist

## Before local demo

- Run scripts/check_all.sh
- Run scripts/pre_import_gate.sh
- Confirm backend starts
- Confirm frontend starts
- Confirm public demo warning banner is visible
- Confirm product status panel loads
- Confirm beta checklist panel loads
- Confirm recommend-v2 returns data
- Confirm search-v2 returns data
- Confirm station suggestions work
- Confirm train stop drilldown works

## Before backend deploy

- Confirm app/requirements.txt exists
- Confirm render.yaml exists
- Confirm live feature flags are false
- Confirm /product/deployment-status works locally
- Confirm RAILYATRA_ALLOWED_ORIGINS is planned

## Before frontend deploy

- Confirm frontend/vercel.json exists
- Confirm frontend build passes
- Confirm VITE_RAILYATRA_API_BASE is planned
- Confirm public warning banner is visible locally
- Confirm frontend does not rely on hardcoded local backend URL inside Phase components

## After backend deploy

Check:

- /
- /health
- /product/status
- /product/beta-checklist
- /product/deployment-status
- /recommend-v2?source=LTT&destination=VVH&direct_limit=3&transfer_limit=1

## After frontend deploy

Check:

- public demo warning banner
- product status panel
- beta checklist panel
- search-v2 preview
- recommend-v2 preview
- station suggestions
- train stop drilldown
- mobile responsiveness

## Must not claim

- live ticket booking
- official railway ticketing
- live seat availability
- live fare
- PNR
- payment
- cancellation

## Approved public label

Real railway route recommendation preview

## Ready-to-share only when

- backend deploy works
- frontend deploy works
- frontend talks to deployed backend
- all public safety warnings are visible
- no false live-booking/payment/PNR claim is visible

