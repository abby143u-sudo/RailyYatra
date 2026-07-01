# RailYatra Phase 7 Local Deploy Ready Checkpoint

Current phase:

Phase 7: actual public demo deployment.

## Next manual action

Run:

    scripts/deploy_preflight.sh
    scripts/github_push_readiness.sh

If GitHub remote exists:

    git push -u origin main

If GitHub remote is missing:

    Create empty GitHub repo
    git remote add origin YOUR_GITHUB_REPO_URL
    git push -u origin main

## After GitHub push

- Deploy backend on Render
- Deploy frontend on Vercel
- Set VITE_RAILYATRA_API_BASE in Vercel
- Set RAILYATRA_ALLOWED_ORIGINS in Render
- Run deployed smoke test

## Public label

Real railway route recommendation preview

## Still not allowed

- live booking claim
- official railway booking claim
- payment claim
- PNR claim
- live fare claim
- live seat availability claim
