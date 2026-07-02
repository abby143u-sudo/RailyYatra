# RailYatra Phase 11 Managed PostgreSQL Migration Plan

Status: PLANNED

Current state:

- Feedback and analytics use lightweight runtime SQLite.
- Admin summary reads feedback and analytics through backend APIs.
- SQLite is acceptable for demo persistence, but not the final production database.

Target state:

Move product-side data to managed PostgreSQL while keeping the railway read database stable.

Recommended provider options:

- Render PostgreSQL
- Supabase PostgreSQL
- Neon PostgreSQL
- Railway PostgreSQL

Production tables to create first:

1. feedback
   - id
   - type
   - message
   - page
   - source
   - client_created_at
   - server_created_at
   - payload_json

2. analytics_events
   - id
   - type
   - details_json
   - page
   - source
   - client_created_at
   - server_created_at
   - payload_json

3. admin_audit_logs
   - id
   - admin_id
   - action
   - endpoint
   - ip
   - created_at

4. saved_searches
   - id
   - source
   - destination
   - class_code
   - quota
   - created_at

Environment variable:

DATABASE_URL=postgresql://user:password@host:port/database

Safe migration order:

1. Create managed PostgreSQL instance.
2. Add DATABASE_URL on Render.
3. Add PostgreSQL connection module.
4. Add migration script to create tables.
5. Move feedback storage from SQLite to PostgreSQL when DATABASE_URL exists.
6. Move analytics storage from SQLite to PostgreSQL when DATABASE_URL exists.
7. Keep SQLite fallback for local development.
8. Add admin audit logs.
9. Add protected admin login.

Current code added in this checkpoint:

- app/backend/api/database_config.py
- GET /admin/database-status
- scripts/check_phase11_database_status.py

Production warning:

Do not put DATABASE_URL or admin tokens in frontend code. They must stay in backend environment variables only.
