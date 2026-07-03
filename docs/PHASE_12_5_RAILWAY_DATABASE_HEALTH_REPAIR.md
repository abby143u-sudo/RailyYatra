# RailYatra Phase 12.5 Railway Database Health Repair

Status: ADDED

Reason:

After PostgreSQL was connected successfully, /health reported unhealthy because the deployed SQLite railway database did not contain readable railway tables.

Added:

- scripts/prepare_deploy_database.py
- Deploy-time railway SQLite preparation
- staging_stations
- staging_trains
- staging_train_stops
- legacy stations
- legacy trains
- legacy train_stops
- demo fares

Also patched:

- scripts/migrate_phase12_postgres_demo_store.py now prepares the railway SQLite database before running PostgreSQL feedback/analytics migration.

Why this matters:

PostgreSQL stores product demo feedback and analytics. The railway route engine still needs the railway SQLite database to be readable for route recommendations and health checks.

Next:

Deploy latest commit on Render and verify /health returns healthy.
