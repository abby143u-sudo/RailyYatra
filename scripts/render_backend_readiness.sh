#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "RailYatra Render backend readiness check"
echo "Mode: local backend deploy config validation"

rm -rf frontend/dist
rm -f docs/.PROJECT_STATUS.md.swp

test -f render.yaml
test -f app/requirements.txt
test -f app/backend/api/main.py
test -f docs/RENDER_BACKEND_SETUP.md

echo "Checking render.yaml required phrases..."
grep -q "rootDir: app" render.yaml
grep -q "pip install -r requirements.txt" render.yaml
grep -q "uvicorn backend.api.main:app --host 0.0.0.0 --port \$PORT" render.yaml
grep -q "RAILYATRA_LIVE_BOOKING_ENABLED" render.yaml
grep -q "RAILYATRA_PAYMENT_ENABLED" render.yaml

echo "Checking app requirements..."
grep -q "fastapi" app/requirements.txt
grep -q "uvicorn" app/requirements.txt
grep -q "networkx" app/requirements.txt

echo "Running backend endpoint smoke tests..."
python3 scripts/smoke_product_status.py
python3 scripts/smoke_beta_checklist.py
python3 scripts/smoke_deployment_config.py
python3 scripts/smoke_recommend_v2.py
python3 scripts/smoke_search_v2.py

echo ""
echo "RENDER BACKEND READINESS RESULT: PASS"
echo "Safe next action: create Render Web Service using docs/RENDER_BACKEND_SETUP.md."
