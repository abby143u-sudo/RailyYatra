# RailYatra Phase 3 Plan

Phase 3 goal:

Connect validated staging railway data into the real RailYatra graph/search engine.

## Current Input

Staging tables:

- staging_stations
- staging_trains
- staging_train_stops

Expected scale:

- stations: about 8990
- trains: about 5208
- train stops/schedules: about 417080

## Phase 3 Steps

1. Inspect current backend search and graph data flow.
2. Create read-only staging query helpers.
3. Build staging graph loader.
4. Build route search from staging train stops.
5. Add backend endpoint switch for staging-powered search.
6. Keep existing demo search safe until staging search passes tests.
7. Add backend smoke tests for staging-powered search.
8. Connect frontend to real staging-powered route results.
9. Optimize search performance.
10. Document Phase 3 completion.

## Safety Rules

- Do not delete production tables.
- Do not remove current working demo endpoints.
- Add staging-powered search beside current search first.
- Switch frontend only after staging search passes smoke tests.
- Keep scripts/check_all.sh passing after every step.

## First Implementation Step

Create read-only staging query helpers for:

- station lookup
- train lookup
- stops by train
- trains by source/destination station
- graph edge preview
