# Backend deployment on Vercel — design

**Date:** 2026-07-13
**Status:** Approved

## Problem

The React frontend is deployed on Vercel (root directory `Real/frontend`). The
model that powers the "Submit" button lives in a separate Python backend
(`Real/backend/app.py`, a FastAPI app calling `solver.py` + `model.py`) that
only runs on the developer's machine. In production the frontend posts to a
hardcoded `http://localhost:8000/run`, which does not exist, so the app's core
feature is non-functional once deployed.

The model takes ~70 seconds to run per request (parameters come from the form).

## Constraints

- Free hosting only.
- Vercel free (Hobby) Python functions now default to and cap at **300s**
  execution time under Fluid Compute — comfortably above the 70s runtime.
- Function instance on Hobby: 1 vCPU / 2 GB. The solver's hot path is
  single-threaded, element-wise NumPy (Python loops over grid points), so
  per-core speed is close to the dev machine; peak memory ~100 MB.

## Decision

Deploy the Python model as a **Vercel Python Serverless Function inside the
existing frontend project**, sharing the frontend's origin. The React static
build and the function ship from one Vercel project.

Same origin ⇒ **no CORS and no backend URL to configure** — both currently
broken (CORS allows only `localhost:3000`; fetch URL hardcoded to
`localhost:8000`) and both disappear with this design.

### Rejected alternatives

- **Separate Vercel project for the backend** — keeps repo structure clean but
  reintroduces CORS + an env-var backend URL and a second dashboard.
- **Off-Vercel free host (Render / Hugging Face Spaces)** — more CPU/RAM
  headroom but cold-start spin-down, CORS, and a second platform. Unnecessary
  now that a free Vercel function covers the 70s runtime.

## Design

### File layout

```
Real/frontend/
├─ api/
│  ├─ run.py            # NEW: Vercel Python function, serves /api/run
│  └─ _model/           # underscore ⇒ not exposed as a route
│     ├─ solver.py      # MOVED from backend/, unchanged
│     └─ model.py       # MOVED from backend/, unchanged
├─ requirements.txt     # NEW: numpy (pinned to tested version)
├─ vercel.json          # NEW: maxDuration 300 for api/run.py
├─ src/pages/Inputs.js  # one-line fetch URL change
└─ package.json
```

`api/run.py` adds its `_model/` directory to `sys.path` and imports `solver`
and `model` as top-level modules, so both moved files stay byte-for-byte
unchanged.

### Function (`api/run.py`)

Native Vercel Python handler (`BaseHTTPRequestHandler`) — no FastAPI/uvicorn,
dropping three dependencies and shrinking cold start. Behavior:

1. Read JSON body (`{param: number, …}`, the shape the form already sends).
2. Validate expected fields are present and numeric → **400** `{"error": …}`.
3. Run `solve_model()` then `simulate()` (identical to today's `app.py`).
4. Return **200** `{"sim": {…series…}}` — the shape the frontend already reads
   via `setResult(data.sim)`.
5. On solver exception → **500** `{"error": str(e)}` so the UI error banner
   shows a message instead of hanging.

`vercel.json` pins `maxDuration: 300` for `api/run.py`.

### Frontend change

[Inputs.js:106] — `fetch('http://localhost:8000/run', …)` →
`fetch('/api/run', …)`. Relative URL works in local dev and production alike.

### Local development

Standardize on `vercel dev`, which serves the CRA build and the Python function
on one port (same origin locally too). Replaces the old
`npm start` + `uvicorn` + Express workflow.

### Retired

- `backend/server.js` — dead Express stub (incomplete, wrong port/route).
- `backend/app.py` — replaced by `api/run.py`.
- `backend/` folder once `solver.py`/`model.py` move out.
- `io_utils.py` is validation-only (parses MATLAB reference outputs; not
  imported by the app). Preserved under `Real/tools/`, not deployed.

## Risks & non-goals

- **1 vCPU speed:** if a large-grid run approaches 300s, fall back to trimming
  default grid sizes or an async job pattern. Out of scope now.
- **Free compute allowance:** ~70 CPU-sec/run is fine for research use; not
  hardened against heavy public traffic.
- **No async/polling, auth, or caching** this iteration — synchronous request,
  matching current behavior.

## Verification

1. `vercel dev` locally → submit the form → results table populates.
2. Vercel **preview** deploy → same check against the real function.
3. Bad input returns a clean JSON error, not a hang.
