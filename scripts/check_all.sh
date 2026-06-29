#!/bin/sh

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || {
  printf '%s\n' 'FAIL: could not locate the scripts directory' >&2
  exit 1
}

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd) || {
  printf '%s\n' 'FAIL: could not locate the repository root' >&2
  exit 1
}

cd "$REPO_ROOT" || {
  printf '%s\n' 'FAIL: could not enter the repository root' >&2
  exit 1
}

cleanup() {
  rm -rf "$REPO_ROOT/frontend/dist"
}

trap cleanup EXIT

backend_status=0
migration_status=0
ingestion_status=0
import_status=0
frontend_status=0

printf '%s\n' '' '=== 1/5 Backend smoke test ==='
python3 scripts/smoke_backend.py || backend_status=$?
if [ "$backend_status" -eq 0 ]; then
  printf '%s\n' 'PASS: backend smoke test'
else
  printf 'FAIL: backend smoke test exited with status %s\n' "$backend_status" >&2
fi

printf '%s\n' '' '=== 2/5 Migration safety check ==='
python3 scripts/smoke_migrations.py || migration_status=$?
if [ "$migration_status" -eq 0 ]; then
  printf '%s\n' 'PASS: migration safety check'
else
  printf 'FAIL: migration safety check exited with status %s\n' \
    "$migration_status" >&2
fi

printf '%s\n' '' '=== 3/5 Ingestion smoke test ==='
python3 scripts/smoke_ingestion.py || ingestion_status=$?
if [ "$ingestion_status" -eq 0 ]; then
  printf '%s\n' 'PASS: ingestion smoke test'
else
  printf 'FAIL: ingestion smoke test exited with status %s\n' \
    "$ingestion_status" >&2
fi

printf '%s\n' '' '=== 4/5 Dry-run railway data import ==='
python3 scripts/import_railway_data.py --dry-run || import_status=$?
if [ "$import_status" -eq 0 ]; then
  printf '%s\n' 'PASS: dry-run railway data import'
else
  printf 'FAIL: dry-run railway data import exited with status %s\n' \
    "$import_status" >&2
fi

printf '%s\n' '' '=== 5/5 Frontend smoke test ==='
scripts/smoke_frontend.sh || frontend_status=$?
if [ "$frontend_status" -eq 0 ]; then
  printf '%s\n' 'PASS: frontend smoke test'
else
  printf 'FAIL: frontend smoke test exited with status %s\n' \
    "$frontend_status" >&2
fi

cleanup

printf '%s\n' '' '=== Final result ==='

if [ "$backend_status" -eq 0 ] \
  && [ "$migration_status" -eq 0 ] \
  && [ "$ingestion_status" -eq 0 ] \
  && [ "$import_status" -eq 0 ] \
  && [ "$frontend_status" -eq 0 ]; then
  printf '%s\n' 'PASS: all RailYatra checks completed successfully'
  exit 0
fi

printf 'FAIL: backend=%s, migration=%s, ingestion=%s, import=%s, frontend=%s\n' \
  "$backend_status" "$migration_status" "$ingestion_status" "$import_status" \
  "$frontend_status" >&2
exit 1
