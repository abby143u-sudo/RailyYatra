# RailYatra Ingestion Plan

## Goal

Build a safe, idempotent, transactional railway data importer for RailYatra.

The importer must improve data quality without breaking the existing working API, frontend, SQLite database, or route graph.

## Current Data Flow

RailYatra currently uses SQLite database data from:

- app/railyatra.db
- app/data/raw/stations.json
- app/data/raw/trains.json
- app/data/raw/schedules.json

The current dry-run inspection reports:

- 8,990 stations
- 5,208 trains
- 417,080 schedules/stops
- some missing station coordinates
- many missing station states
- some missing arrival/departure fields in schedules

## Existing Safety Tools

Use these commands before any real importer work:

    scripts/check_all.sh
    python3 scripts/backup_database.py
    python3 scripts/run_migrations.py --dry-run
    python3 scripts/import_railway_data.py --dry-run
    python3 scripts/smoke_ingestion.py
    python3 scripts/smoke_backend.py
    scripts/smoke_frontend.sh

## Safety Rules

- Never edit archive_legacy/.
- Never manually edit app/railyatra.db.
- Never commit backups/.
- Never commit frontend/dist.
- Never run destructive SQL.
- Never alter stations, trains, train_stops, or official_fares without explicit approval.
- Always run dry-run before database write.
- Always create backup before database write.
- Real import must be explicit, never default.
- Importer must be idempotent.
- Importer must be transactional.
- Failed import must roll back cleanly.

## Phase 1: Read-Only Validation

Already started.

Tasks:

- Read raw JSON files
- Count stations, trains, schedules
- Report missing fields
- Report invalid records
- Report duplicate station codes
- Report duplicate train numbers
- Report invalid schedule rows
- Keep database untouched

Current scripts:

    python3 scripts/smoke_ingestion.py
    python3 scripts/import_railway_data.py --dry-run

## Phase 2: Metadata Migration

Already scaffolded.

Metadata tables:

- ingestion_runs
- ingestion_source_files
- ingestion_issues

Purpose:

- track import attempts
- track raw file fingerprints
- track warnings/errors
- make imports auditable

Current commands:

    python3 scripts/run_migrations.py --dry-run
    python3 scripts/run_migrations.py --apply

## Phase 3: Importer Dry-Run Report

Before writing data, importer should generate a report containing:

- files used
- file sizes
- file checksums
- record counts
- duplicate counts
- missing-field counts
- records to insert
- records to update
- records to skip
- fatal errors
- non-fatal warnings

No database writes in this phase.

## Phase 4: Transactional Metadata Write

First actual database write should only insert one ingestion run record and related source file metadata.

It should not modify railway tables yet.

Required behavior:

- create backup
- start transaction
- insert ingestion_runs row
- insert ingestion_source_files rows
- insert ingestion_issues rows
- commit on success
- rollback on failure

## Phase 5: Normalized Railway Data Import

Only after metadata write is proven safe.

Possible target improvements:

- station state enrichment
- station coordinate validation
- train source/destination verification
- schedule row cleanup
- running-day structure
- fare coverage expansion

Existing route behavior must remain compatible.

## Phase 6: Data Quality Reports

Create reports for:

- stations missing state
- stations missing coordinates
- trains missing source/destination
- schedules missing arrival/departure
- trains without stops
- stops without stations
- duplicate train numbers
- duplicate station codes

## Phase 7: API Integration

Only after importer is stable.

Possible API improvements:

- expose ingestion health in /health
- expose data quality summary
- expose last ingestion run metadata
- improve station search using enriched fields

Do not modify app/backend/api/main.py until importer and migrations are stable.

## Definition of Done

The ingestion pipeline is ready when:

- scripts/check_all.sh passes
- dry-run import is deterministic
- migration dry-run is safe
- database backup works
- metadata migration applies safely
- import can run twice without duplicates
- failed import rolls back
- backend smoke test passes after import
- frontend build passes after import
