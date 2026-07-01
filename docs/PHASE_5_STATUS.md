# RailYatra Phase 5 Status

Phase 5 goal:

Prepare RailYatra for public beta preview while clearly separating real route recommendation demo capabilities from live ticket booking, PNR, payment, fare and seat availability claims.

## Completed

- Product status backend helper
- `/product/status` endpoint
- Public beta checklist backend helper
- `/product/beta-checklist` endpoint
- Frontend product status panel
- Frontend public beta checklist panel
- Product readiness smoke test
- Frontend product status smoke test
- Beta checklist smoke test
- Frontend beta checklist smoke test
- Safety checks wired into `scripts/check_all.sh`
- Safety checks wired into `scripts/pre_import_gate.sh`

## Current Product Status

RailYatra is ready for:

- real railway route recommendation preview
- demo to users
- demo to investors
- search-v2 route preview
- recommend-v2 ranked route preview
- station suggestions
- train stop drilldown
- public beta explanation panels

RailYatra is not ready for:

- live ticket booking
- live fare
- live seat availability
- PNR
- payment
- cancellation
- claiming official booking capability

## Important Endpoints

- `/search`
- `/search-v2`
- `/recommend-v2`
- `/product/status`
- `/product/beta-checklist`
- `/staging/health`
- `/staging/stations`
- `/staging/direct`
- `/staging/search`
- `/staging/trains/{train_number}/stops`

## Frontend Panels Added

- Phase 3 real railway data staging card
- Phase 3 direct train preview
- Phase 3 search-v2 route preview
- Phase 4 recommend-v2 preview
- Phase 5 product status panel
- Phase 5 beta checklist panel

## Safety Rules Preserved

- Legacy `/search` remains available.
- `/search-v2` remains available.
- `/recommend-v2` is separate from legacy `/search`.
- Product status blocks false live-booking claims.
- Beta checklist blocks false ticket-payment claims.
- Production railway tables remain protected.
- Build output `frontend/dist` is removed before commit.
- All safety smoke tests must pass before moving forward.

## Current Data Scale

- Stations: 8990
- Trains: 5208
- Train stops: 417080

## Public Beta Label

Recommended label:

`Real railway route recommendation preview`

Avoid these labels for now:

- live booking app
- official railway ticketing app
- PNR app
- seat availability app
- payment-enabled ticketing platform

## Next Phase

Phase 6 should prepare deployment and production demo packaging.

Recommended next work:

- add `.env.example`
- add backend CORS configuration
- add deployment notes
- add public beta launch checklist
- add demo script
- add clean README quickstart
- add production warning banners
- choose deployment target
