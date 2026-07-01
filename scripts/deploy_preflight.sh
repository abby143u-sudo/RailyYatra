#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "RailYatra Phase 7 deploy preflight"
echo "Mode: local deployment readiness check"
echo ""

rm -rf frontend/dist
rm -f docs/.PROJECT_STATUS.md.swp

echo "Git branch:"
git branch --show-current

echo ""
echo "Git remote:"
git remote -v || true

echo ""
echo "Git status before checks:"
git status --short

echo ""
echo "Running focused deployment smokes..."
python3 scripts/smoke_public_demo_docs.py
python3 scripts/smoke_deployment_packaging.py
python3 scripts/smoke_public_demo_banner.py
python3 scripts/smoke_frontend_api_config.py
python3 scripts/smoke_deployment_config.py
python3 scripts/smoke_product_status.py
python3 scripts/smoke_beta_checklist.py
python3 scripts/smoke_recommend_v2.py
python3 scripts/smoke_search_v2.py
python3 scripts/smoke_deployed_public_demo.py

echo ""
echo "Building frontend..."
npm --prefix frontend run build

echo ""
echo "Running full project checks..."
scripts/check_all.sh

echo ""
echo "Running pre-import safety gate..."
scripts/pre_import_gate.sh

rm -rf frontend/dist
rm -f docs/.PROJECT_STATUS.md.swp

echo ""
echo "Git status after checks:"
git status --short

echo ""
echo "PHASE 7 DEPLOY PREFLIGHT RESULT: PASS"
echo "Safe next action: push GitHub repo, deploy backend on Render, deploy frontend on Vercel."
echo "Backend: Render rootDir app, build pip install -r requirements.txt, start uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT"
echo "Frontend: Vercel rootDir frontend, build npm run build, output dist."
echo "Do not claim live booking/payment/PNR/fare/availability yet."
