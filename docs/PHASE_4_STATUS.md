# RailYatra Phase 4 Status

Phase 4 goal:

Turn the Phase 3 route/search engine into a recommendation layer that can rank routes, explain choices, and clearly warn users about what is not live yet.

## Completed

- Recommendation v2 backend engine
- `/recommend-v2` endpoint
- Ranked recommendations
- Confidence score and confidence level
- Transfer safety labels
- Recommendation reasons
- Live booking/fare/availability not-connected warning
- Legacy `/search` protection
- `/search-v2` remains available
- Frontend recommendation preview panel
- Frontend station suggestions in recommendation panel
- Frontend recommendation smoke test
- Backend recommendation smoke test
- Full check integration through `scripts/check_all.sh`
- Safety gate integration through `scripts/pre_import_gate.sh`

## Current Important Endpoints

- `/search`
- `/search-v2`
- `/recommend-v2`
- `/staging/health`
- `/staging/stations`
- `/staging/direct`
- `/staging/search`
- `/staging/trains/{train_number}/stops`

## Recommendation v2 Output Includes

- recommendation rank
- route type
- source
- destination
- transfer station, if any
- route legs
- total stop count
- total distance
- confidence score
- confidence level
- transfer safety label
- reasons
- booking readiness warning

## Safety Rules Preserved

- Legacy `/search` remains unchanged.
- `/recommend-v2` is separate from `/search` and `/search-v2`.
- Staging route engine is read-only.
- Production railway tables are protected.
- Live booking is not falsely claimed.
- Live availability and live fare are explicitly marked as not connected.
- Frontend build artifacts are removed before commit.

## Known Limitations

- Recommendation scoring is still rule-based.
- Transfer-time safety is limited by missing arrival/departure fields in raw data.
- Live fare, live availability, PNR, booking, cancellation and payment are not connected.
- One-transfer route search is bounded to keep local performance safe.
- This is a production-candidate recommendation layer, not final public travel booking logic.

## Next Phase

Phase 5 should merge the polished recommendation experience into the main user journey.

Recommended next work:

- make `/recommend-v2` the main frontend search option
- keep legacy search as fallback
- add user-facing mode switch: demo search vs real-data search
- polish result cards for public demo
- add clean empty states for invalid station pairs
- add public beta readiness checklist
- prepare deployment configuration
