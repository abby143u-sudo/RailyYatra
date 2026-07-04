# RailYatra Live Route Search Final Verified

Status: VERIFIED

Verified:

- Live backend /search returns frontend-safe route shape.
- train_no exists at route, train and leg levels.
- train_name exists at route, train and leg levels.
- best_direct is populated.
- Live Vercel frontend responds.
- Local frontend production build passes.

Manual browser check:

- Open https://raily-yatra.vercel.app
- Hard refresh with Cmd + Shift + R
- Search PNBE to NDLS
- Page should not blank.
- Route result should render.
