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
run_step "Staging query helper smoke test" python3 scripts/smoke_staging_queries.py
run_step "Staging route index smoke test" python3 scripts/smoke_staging_route_indexes.py
run_step "Staging route engine smoke test" python3 scripts/smoke_staging_route_engine.py
run_step "Search-v2 smoke test" python3 scripts/smoke_search_v2.py
run_step "Recommend-v2 smoke test" python3 scripts/smoke_recommend_v2.py
run_step "Product status smoke test" python3 scripts/smoke_product_status.py
run_step "Deployment config smoke test" python3 scripts/smoke_deployment_config.py
run_step "Deployment packaging smoke test" python3 scripts/smoke_deployment_packaging.py
run_step "Public demo docs smoke test" python3 scripts/smoke_public_demo_docs.py
run_step "Deployed public demo smoke test" python3 scripts/smoke_deployed_public_demo.py
run_step "Phase 7 deploy preflight docs smoke test" python3 scripts/smoke_phase7_deploy_preflight.py
run_step "GitHub push readiness smoke test" python3 scripts/smoke_github_push_readiness.py
run_step "Frontend API config smoke test" python3 scripts/smoke_frontend_api_config.py
run_step "Public demo banner smoke test" python3 scripts/smoke_public_demo_banner.py
run_step "Beta checklist smoke test" python3 scripts/smoke_beta_checklist.py
run_step "Frontend beta checklist smoke test" python3 scripts/smoke_frontend_beta_checklist.py
run_step "Frontend product status smoke test" python3 scripts/smoke_frontend_product_status.py
run_step "Frontend recommend-v2 smoke test" python3 scripts/smoke_frontend_recommend_v2.py
run_step "Frontend search-v2 smoke test" python3 scripts/smoke_frontend_search_v2.py
run_step "Staging API smoke test" python3 scripts/smoke_staging_api.py
run_step "Metadata writer smoke test" python3 scripts/smoke_metadata_writer.py
run_step "Ingestion metadata verifier dry-run" python3 scripts/verify_ingestion_metadata.py --dry-run
run_step "Frontend smoke test" scripts/smoke_frontend.sh

cleanup

printf '\n========================================\n'
printf 'FINAL RESULT: PASS\n'
printf 'frontend/dist removed\n'
printf '========================================\n'
