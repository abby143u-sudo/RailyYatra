# RailYatra Frontend Stability Checkpoint

Status: STABLE PUBLIC DEMO PRIORITY

Decision:
The main top From/To autocomplete has been disabled temporarily because the suggestion dropdown was crashing the React app when more than one station letter was typed.

Current stable behavior:
- Main From/To search accepts station codes manually.
- PNBE and NDLS typing should not blank the page.
- Main search can still submit manually entered station codes.
- Phase 3 and Phase 4 preview boxes can keep their own autocomplete behavior separately.

Reason:
Public demo stability is more important than autocomplete at this stage.

Next safe improvement:
Build a new isolated station autocomplete component and test it separately before reconnecting it to the main search.

## Safe station lookup test

A new isolated SafeStationLookupTest component has been added. It tests the station suggestion endpoint separately from the main From/To search so autocomplete can be validated without risking the public demo search form.

## Safe main autocomplete reconnected

The main From/To search now uses SafeStationInput instead of the old crashing suggestion panel. It fetches station suggestions safely from `/staging/stations` and should not blank the page when typing PNBE or NDLS.

