# RailYatra Phase 10 SQLite Persistence

Status: ADDED

Upgrade:

- Feedback storage moved from JSONL to SQLite
- Analytics storage moved from JSONL to SQLite
- Shared backend store added at app/backend/api/demo_store.py
- Runtime database path: app/data/demo_events.db

Smoke script:

- scripts/smoke_phase10_sqlite_persistence.py

Production note:

This is a lightweight runtime SQLite persistence layer. For serious production, move feedback and analytics to managed PostgreSQL or another durable managed database.
