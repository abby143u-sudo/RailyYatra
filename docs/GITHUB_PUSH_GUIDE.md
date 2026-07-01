# RailYatra GitHub Push Guide

Current phase:

Phase 7: actual public demo deployment.

## Goal

Push the clean RailYatra repository to GitHub before Render and Vercel deployment.

## Step 1: Run local deploy preflight

    scripts/deploy_preflight.sh

## Step 2: Check GitHub push readiness

    scripts/github_push_readiness.sh

If it says READY, run:

    git push -u origin main

If it says NEEDS_REMOTE, create an empty GitHub repository and add remote:

    git remote add origin YOUR_GITHUB_REPO_URL
    git push -u origin main

## Step 3: After push

Use this GitHub repository for:

- Render backend deployment
- Vercel frontend deployment

## Do not commit

- frontend/dist
- .env
- local secrets
- temporary swap files

## Current public label

Real railway route recommendation preview

## Still blocked

- live booking
- payment
- PNR
- live fare
- live seat availability
- cancellation
