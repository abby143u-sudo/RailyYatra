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

printf '\nRailYatra CI-safe project check\n'
printf 'Project root: %s\n' "$ROOT_DIR"
printf 'Production railway SQLite database: not required\n'

run_step \
  "Backend CI smoke test" \
  env RAILYATRA_CI=1 python3 scripts/smoke_backend.py

run_step \
  "Authentication test suite" \
  python3 -m unittest discover -s tests -p "test_auth*.py" -v

run_step \
  "Beta feedback smoke test" \
  python3 scripts/smoke_beta_feedback.py

run_step \
  "Migration smoke test" \
  python3 scripts/smoke_migrations.py

run_step \
  "Migration runner dry-run" \
  python3 scripts/run_migrations.py --dry-run

run_step \
  "Ingestion smoke test" \
  python3 scripts/smoke_ingestion.py

run_step \
  "Railway data import dry-run" \
  python3 scripts/import_railway_data.py --dry-run

run_step \
  "Staging planner smoke test" \
  python3 scripts/smoke_staging_planner.py

run_step \
  "Staging apply safety smoke test" \
  python3 scripts/smoke_staging_apply.py

run_step \
  "Deployment packaging smoke test" \
  python3 scripts/smoke_deployment_packaging.py

run_step \
  "Public demo docs smoke test" \
  python3 scripts/smoke_public_demo_docs.py

run_step \
  "Frontend API config smoke test" \
  python3 scripts/smoke_frontend_api_config.py

run_step \
  "Account frontend contract smoke test" \
  python3 scripts/smoke_account_frontend_contract.py

run_step \
  "Frontend smoke test" \
  scripts/smoke_frontend.sh

cleanup

printf '\n========================================\n'
printf 'CI RESULT: PASS\n'
printf 'frontend/dist removed\n'
printf '========================================\n'
