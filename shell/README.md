# Shared static demo shell (`shell/`)

This folder is tracked **inside** the Data Cleaning Toolkit repository. It owns shared layout chrome (sidebar identity, hero frame, optional related links); product behavior stays in **`src/`** (unchanged Streamlit flow).

## Files

- `index.html` — template with placeholders
- `shell.css`, `demo-content.css`, `shell.js` — styling and light UI behavior
- `favicon.svg` — icon (also reused as labs-safe avatar asset for commercial profile)
- `profile.json` — fallback recruiter-aligned profile (`render-shell.mjs`)
- `profiles/*.json` — named profiles (`recruiter`, `commercial`)
- `projects/data-cleaning.json` — recruiter + commercial copy & link variants
- `body/data-cleaning.html` — recruiter-facing technical narrative
- `body/data-cleaning-commercial.html` — labs-facing narrative
- `render-shell.mjs` — hydrates templates into a deployment folder

## Render flow

Requires **Node.js 18+** (built-in `fs/promises`).

From the repository root:

**Recruiter static** (planned host `data-cleaning.vahdetkaratas.com`) → `layout-shell/`:

```bash
node shell/render-shell.mjs \
  --project shell/projects/data-cleaning.json \
  --body shell/body/data-cleaning.html \
  --out layout-shell \
  --profile recruiter
```

**Commercial static** (planned host `data-cleaning.vahdetlabs.com`) → `layout-shell-commercial/`:

```bash
node shell/render-shell.mjs \
  --project shell/projects/data-cleaning.json \
  --body shell/body/data-cleaning-commercial.html \
  --out layout-shell-commercial \
  --profile commercial
```

Each run writes fresh `index.html`, copies assets, emits `profile.json` matching the chosen profile.

## Separation rules recap

- **Commercial** output contains **no** `vahdetkaratas.com` links/images and avoids hire-me tone.
- **Recruiter** output may cite the hosted Streamlit demo (`cleaning-data.vahdetkaratas.com`) and CV site.
- **Commercial** Streamlit demo link uses **`cleaning-data.vahdetlabs.com`** only (no `vahdetkaratas.com` hosts in that build).
- The **live app** stays separate Streamlit—not embedded inside these static bundles.
