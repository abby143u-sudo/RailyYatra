# RailYatra Production Database Architecture Plan

Status: PLANNED

Current state:

- Railway search data runs from the deployed backend database/runtime files.
- Feedback and analytics demo events use lightweight SQLite persistence.
- SQLite is acceptable for Phase 10 demo persistence but not final production durability.

Production target:

Move feedback, analytics, admin data, users and future booking-related records to managed PostgreSQL.

Recommended database layers:

1. Core railway read database
   - stations
   - trains
   - train_stops
   - route metadata
   - schedule cache

2. Product database
   - users
   - saved_searches
   - saved_routes
   - feedback
   - analytics_events
   - admin_audit_logs

3. Future live integration cache
   - availability_cache
   - fare_cache
   - delay_cache
   - provider_response_logs

4. Future booking boundary tables
   - booking_intents
   - payment_attempts
   - pnr_lookup_requests
   - cancellation_requests

Important boundary:

RailYatra should not store sensitive payment data directly. Use payment provider references only.

Migration path:

Step 1: Keep existing SQLite for demo events.
Step 2: Add DATABASE_URL support.
Step 3: Add PostgreSQL connection module.
Step 4: Create tables through migration script.
Step 5: Move feedback API to PostgreSQL.
Step 6: Move analytics API to PostgreSQL.
Step 7: Move admin summaries to PostgreSQL queries.
Step 8: Keep SQLite fallback only for local development.

Production database recommendation:

- Render PostgreSQL, Supabase PostgreSQL, Neon, or Railway PostgreSQL.
- Start with managed PostgreSQL before building live booking or user accounts.
