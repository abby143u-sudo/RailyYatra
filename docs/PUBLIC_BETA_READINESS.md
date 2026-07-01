# RailYatra Public Beta Readiness

## Demo-ready

RailYatra can be shown as:

- real railway route recommendation preview
- route search proof-of-concept
- search-v2 demo
- recommend-v2 demo
- real-data railway journey planning preview

## Not demo-ready as

Do not present it as:

- live ticket booking app
- official railway booking app
- payment-enabled ticketing product
- PNR tracking product
- live seat availability product
- live fare product

## Public Demo Script

1. Open backend.
2. Open frontend.
3. Show product status panel.
4. Show beta checklist panel.
5. Search sample route in search-v2 preview.
6. Show ranked recommendation in recommend-v2 preview.
7. Explain confidence, transfer safety and reasons.
8. Show train stop drilldown.
9. Clearly say live booking is not connected yet.

## Required local checks before demo

Run:

    scripts/check_all.sh
    scripts/pre_import_gate.sh

Expected:

- both should pass
- `frontend/dist` should not be committed
- production railway tables should remain protected
- live booking claims should remain blocked
