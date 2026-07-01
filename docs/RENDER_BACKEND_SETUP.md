# RailYatra Render Backend Setup

Current phase:

Phase 7: actual public demo deployment.

## Goal

Deploy the RailYatra backend API on Render.

## Render service type

Create a new Web Service.

## Source

Use the GitHub repository connected to this local repo.

## Settings

- Name: railyatra-backend
- Environment: Python
- Root Directory: app
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT

## Environment variables

Set these in Render:

    RAILYATRA_ENV=production
    RAILYATRA_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
    RAILYATRA_LIVE_BOOKING_ENABLED=false
    RAILYATRA_LIVE_FARE_ENABLED=false
    RAILYATRA_LIVE_AVAILABILITY_ENABLED=false
    RAILYATRA_PNR_ENABLED=false
    RAILYATRA_PAYMENT_ENABLED=false

After Vercel frontend deployment, replace RAILYATRA_ALLOWED_ORIGINS with the Vercel frontend URL.

## Backend URLs to test after Render deploy

- /
- /health
- /product/status
- /product/beta-checklist
- /product/deployment-status
- /recommend-v2?source=LTT&destination=VVH&direct_limit=3&transfer_limit=1

## Must remain false

- live booking
- live fare
- live availability
- PNR
- payment

## Approved public label

Real railway route recommendation preview
