# RailYatra Real Railway Data Import Design

## Purpose

This document defines the safe design for importing normalized railway data into RailYatra.

The current project already has:

- working backend smoke tests
- working frontend production build
- raw railway data inspection
- migration dry-run safety
- metadata-only ingestion writer
- ingestion metadata verifier
- pre-import safety gate

Real railway data import must not begin until this design is reviewed.

## Current Raw Data

Raw files:

- app/data/raw/stations.json
- app/data/raw/trains.json
- app/data/raw/schedules.json

Latest inspected counts:

- stations: 8990
- trains: 5208
- schedules/stops: 417080

Known data quality issues:

- 1 station missing name
- 4593 stations missing state
- 293 stations missing coordinates
- 1 train missing name
- 27835 schedules missing arrival
- 27827 schedules missing departure

Blocking quality issues currently reported as zero:

- stations missing code
- trains missing number
- trains missing source
- trains missing destination
- schedules missing train number
- schedules missing station code

## Safety Rule

No real import script should write to train, station, stop, route, fare, or graph tables unless all of these pass first:

    scripts/pre_import_gate.sh

Required checks inside the gate:

- backend smoke test
- migration smoke test
- migration runner dry-run
- raw railway ingestion inspection
- railway data import dry-run
- metadata writer smoke test
- ingestion metadata verifier dry-run
- frontend production build

## Import Mode Design

The real importer should support these modes:

### 1. Dry-run mode

Command idea:

    python3 scripts/import_railway_data.py --dry-run

Rules:

- read raw JSON only
- inspect counts
- inspect data quality issues
- print planned inserts and updates
- do not open database for writing
- do not modify railway data tables

### 2. Metadata-only mode

Command idea:

    python3 scripts/write_ingestion_metadata.py --apply

Rules:

- create backup before writing
- write only ingestion audit metadata
- do not modify real railway tables
- verify with:

    python3 scripts/verify_ingestion_metadata.py

### 3. Staging import mode

Command idea:

    python3 scripts/import_railway_data.py --stage

Rules:

- create backup before writing
- write only to staging tables
- do not touch production railway tables
- validate row counts
- validate required keys
- validate duplicate station codes
- validate duplicate train numbers
- validate orphan schedule station codes
- validate orphan schedule train numbers
- rollback transaction if validation fails

### 4. Promote mode

Command idea:

    python3 scripts/import_railway_data.py --promote

Rules:

- allowed only after staging validation passes
- create backup before writing
- use transaction
- replace or upsert normalized production tables safely
- rollback on any failure
- run backend smoke test after promote
- run frontend smoke test after promote

## Proposed Staging Tables

The first real import should write to staging tables only:

- staging_stations
- staging_trains
- staging_train_stops

Staging table rules:

- safe to drop/recreate only staging tables
- production tables must not be dropped
- production data must not be deleted
- staging import must be repeatable

## Proposed Production Tables

Production normalized tables should be reviewed before implementation:

### stations

Suggested fields:

- code
- name
- state
- latitude
- longitude
- source_file
- updated_at

### trains

Suggested fields:

- train_number
- train_name
- source_station_code
- destination_station_code
- train_type
- source_file
- updated_at

### train_stops

Suggested fields:

- train_number
- station_code
- stop_sequence
- arrival
- departure
- distance
- day_offset
- source_file
- updated_at

## Transaction Rules

Every write mode must follow this order:

1. run pre-import gate
2. create database backup
3. start transaction
4. write metadata run row
5. write staging or production data
6. validate row counts
7. validate references
8. commit only if all checks pass
9. rollback if any check fails
10. run smoke tests after successful commit

## Rollback Rules

Rollback must happen if:

- raw file is missing
- JSON parsing fails
- required key missing in blocking fields
- duplicate primary keys found
- orphan train number found in schedules
- orphan station code found in schedules
- row count is unexpectedly low
- backend smoke test fails after import

## Manual Review Before Real Import

Before enabling real import writes, manually confirm:

- staging schema is approved
- production schema is approved
- rollback tested
- backup restore tested
- endpoint output checked after import
- frontend route search checked after import

## Next Implementation Step

Build staging migration files only.

Do not write real railway data yet.

Next safe file:

    app/backend/database/migrations/002_staging_import_tables.sql

This migration should create staging tables only.
