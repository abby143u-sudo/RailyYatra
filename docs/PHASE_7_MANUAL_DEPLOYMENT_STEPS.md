# RailYatra Phase 7 Manual Deployment Steps

Current phase:

Phase 7: actual public demo deployment.

## Step 1: Run local preflight

Run:

    scripts/deploy_preflight.sh

Expected result:

    PHASE 7 DEPLOY PREFLIGHT RESULT: PASS

## Step 2: Push code to GitHub

If GitHub remote is not added yet:

    git remote add origin YOUR_GITHUB_REPO_URL

Then push:

    git push -u origin main

## Step 3: Deploy backend on Render

Create a new Render Web Service from the GitHub repo.

Use:

- Root directory: app
- Build command: pip install -r requirements.txt
- Start command: uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT

Backend environment variables:

    RAILYATRA_ENV=production
    RAILYATRA_ALLOWED_ORIGINS=https://your-vercel-frontend-url.vercel.app
    RAILYATRA_LIVE_BOOKING_ENABLED=false
    RAILYATRA_LIVE_FARE_ENABLED=false
    RAILYATRA_LIVE_AVAILABILITY_ENABLED=false
    RAILYATRA_PNR_ENABLED=false
    RAILYATRA_PAYMENT_ENABLED=false

## Step 4: Check backend deployed URLs

Open:

- /
- /health
- /product/status
- /product/beta-checklist
- /product/deployment-status
- /recommend-v2?source=LTT&destination=VVH&direct_limit=3&transfer_limit=1

## Step 5: Deploy frontend on Vercel

Create a new Vercel project from the same GitHub repo.

Use:

- Root directory: frontend
- Framework: Vite
- Build command: npm run build
- Output directory: dist

Frontend environment variable:

    VITE_RAILYATRA_API_BASE=https://your-render-backend-url.onrender.com

## Step 6: Update Render allowed origin

After Vercel gives frontend URL, update Render:

    RAILYATRA_ALLOWED_ORIGINS=https://your-vercel-frontend-url.vercel.app

Then redeploy backend.

## Step 7: Run deployed smoke test

Run:

    RAILYATRA_DEPLOYED_BACKEND_URL=https://your-render-backend-url.onrender.com RAILYATRA_DEPLOYED_FRONTEND_URL=https://your-vercel-frontend-url.vercel.app python3 scripts/smoke_deployed_public_demo.py

Expected result:

    PASS: deployed public demo smoke test completed

## Approved public label

Real railway route recommendation preview

## Never claim yet

- live ticket booking
- official railway booking
- live seat availability
- live fare
- PNR
- payment
- cancellation
