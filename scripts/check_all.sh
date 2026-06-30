#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

run_step() {
  local label="$1"
  shift

  printf '\n========================================\n'
  printf 'RUNNING: %s\n' "$label"
  printf '========================================\n'

  "$@"

  printf 'PASS: %s\n' "$label"
}

cleanup() {
  rm -rf "$ROOT_DIR/frontend/dist"
}

trap cleanup EXIT

printf '\nRailYatra combined project check\n'
printf 'Project root: %s\n' "$ROOT_DIR"

run_step "Backend smoke test" python3 scripts/smoke_backend.py
run_step "Migration smoke test" python3 scripts/smoke_migrations.py
run_step "Migration runner dry-run" python3 scripts/run_migrations.py --dry-run
run_step "Ingestion smoke test" python3 scripts/smoke_ingestion.py
run_step "Railway data import dry-run" python3 scripts/import_railway_data.py --dry-run
run_step "Staging planner smoke test" python3 scripts/smoke_staging_planner.py
run_step "Staging apply skeleton smoke test" python3 scripts/smoke_staging_apply.py
run_step "Staging verifier smoke test" python3 scripts/smoke_staging_verifier.py
run_step "Metadata writer smoke test" python3 scripts/smoke_metadata_writer.py
run_step "Ingestion metadata verifier dry-run" python3 scripts/verify_ingestion_metadata.py --dry-run
run_step "Frontend smoke test" scripts/smoke_frontend.sh

cleanup

printf '\n========================================\n'
printf 'FINAL RESULT: PASS\n'
printf 'frontend/dist removed\n'
printf '========================================\n'
