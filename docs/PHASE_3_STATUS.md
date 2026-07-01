# RailYatra Phase 3 Status

Phase 3 goal:

Connect validated staging railway data into the real route/search engine without breaking the existing MVP search.

## Completed

- Read-only staging query helpers
- Staging health API
- Staging direct-train API
- Staging station search API
- Staging train-stops API
- Real staging route engine
- Direct route search
- Bounded one-transfer route search
- Production-candidate `/search-v2` endpoint
- Frontend Phase 3 staging health card
- Frontend direct-train preview
- Frontend `/search-v2` route preview
- Frontend station suggestions from staging data
- Frontend train stop drilldown
- Composite route lookup indexes
- Backend smoke tests
- Frontend static contract smoke test
- Combined safety checks

## Current Real Data Scale

- Stations: 8990
- Trains: 5208
- Train stops: 417080

## Important Endpoints

- `/staging/health`
- `/staging/stations?q=PATNA`
- `/staging/direct?source=LTT&destination=VVH`
- `/staging/trains/{train_number}/stops`
- `/staging/search?source=LTT&destination=VVH`
- `/search-v2?source=LTT&destination=VVH`

## Safety Rules Still Preserved

- Legacy `/search` remains available.
- `/search-v2` is separate from legacy `/search`.
- Staging APIs are read-only.
- Production railway tables are protected.
- Frontend build artifacts are removed before commit.
- `scripts/check_all.sh` and `scripts/pre_import_gate.sh` must pass before each checkpoint.

## Known Limitations

- One-transfer search is intentionally bounded for performance.
- Timetable transfer-time validation is basic because some arrival/departure values are missing in raw data.
- Live fare, live availability, PNR, and booking are not connected yet.
- Search-v2 is production-candidate, not final public railway booking search.

## Next Phase

Phase 4 should turn `/search-v2` output into a stronger recommendation engine:

- route scoring polish
- transfer safety scoring
- route confidence label
- missing-time warnings
- faster candidate selection
- fare/availability placeholder mapping
- frontend UI cleanup for production use
